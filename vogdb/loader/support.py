import os
import sys
import pandas as pd
import numpy as np

from sqlalchemy import create_engine
from Bio import SeqIO
from sqlalchemy.types import Integer, String, Boolean, Text

"""
Here we create our VOGDB and create all the tables that we are going to use
"""


def generate_db(data_path, db_url):

    # Create an engine object.
    engine = create_engine(db_url)

    with engine.connect() as con:
        # In case there are old tables:
        con.execute("DROP TABLE IF EXISTS NT_seq;")
        con.execute("DROP TABLE IF EXISTS AA_seq;")
        # Todo: Take out the dropping Protein_info
        con.execute("DROP TABLE IF EXISTS Protein_table;")
        con.execute("DROP TABLE IF EXISTS Protein_profile;")
        con.execute("DROP TABLE IF EXISTS Table_mapping;")
        con.execute("DROP TABLE IF EXISTS Member;")
        con.execute("DROP TABLE IF EXISTS VOG_profile;")
        con.execute("DROP TABLE IF EXISTS Species_profile;")
        # for the new tables:
        con.execute("DROP TABLE IF EXISTS Protein_table;")
        con.execute("DROP TABLE IF EXISTS Member;")
        con.execute("DROP TABLE IF EXISTS VOG_table;")
        con.execute("DROP TABLE IF EXISTS Species_table;")


    # ---------------------
    # Species_table generation
    # ----------------------
    # extract Species information from the list
    species_list_df = pd.read_csv(os.path.join(data_path, "vog.species.list"),
                                  sep='\t',
                                  header=0,
                                  names=['SpeciesName', 'TaxonID', 'Phage', 'Source', 'Version']) \
        .assign(Phage=lambda p: p.Phage == 'phage')
    # create a species table in the database

    species_list_df.to_sql(name='Species_table', con=engine, if_exists='replace', index=False, chunksize=1000, dtype={
        'TaxonId': Integer,
        'SpeciesName': String(100),
        'Phage': Boolean,
        'Source': String(100),
        'Version': Integer
    })

    with engine.connect() as con:
        con.execute("""
        ALTER TABLE Species_table 
            MODIFY TaxonID int NOT NULL PRIMARY KEY,
            MODIFY SpeciesName varchar(100) NOT NULL,
            MODIFY Phage bool NOT NULL,
            MODIFY Source varchar(100) NOT NULL,
            MODIFY Version int NOT NULL;
        """)


    print('Species_table table successfully created!')

    # ---------------------
    # Protein_table generation
    # ----------------------

    proteinfile = data_path + "vog.proteins.all.fa"
    prot = []
    for seq_record in SeqIO.parse(proteinfile, "fasta"):
        prot.append([seq_record.id, str(seq_record.seq)])
    df_aa = pd.DataFrame(prot, columns=['ProteinID', 'AASeq'])
    df_aa.set_index("ProteinID")

    genefile = data_path + "vog.genes.all.fa"
    genes = []
    for seq_record in SeqIO.parse(genefile, "fasta"):
        genes.append([seq_record.id, str(seq_record.seq)])
    df_nt = pd.DataFrame(genes, columns=['ProteinID', 'NTSeq'])
    df_nt.set_index('ProteinID')

    prot_df = df_aa.merge(df_nt, on='ProteinID', how='outer')

    # place taxonID in a separate column
    prot_df["TaxonID"] = prot_df["ProteinID"].str.split(".").str[0]

    # create a protein table in the database
    prot_df.to_sql(name='Protein_table', con=engine, if_exists='replace', index=False, chunksize=1000, dtype={
        'ProteinID': String(30),
        'TaxonID': Integer,
        'AASeq': Text(65000),
        'NTSeq': Text(65000),
    })

    with engine.connect() as con:
        con.execute("""
        ALTER TABLE Protein_table
            MODIFY ProteinID varchar(30) NOT NULL PRIMARY KEY,
            MODIFY TaxonID int NOT NULL,
            MODIFY AASeq mediumtext NULL,
            MODIFY NTSeq mediumtext NULL,
            ADD FOREIGN KEY(TaxonID) REFERENCES Species_table(TaxonID),
            ADD INDEX(ProteinID),
            ADD INDEX(TaxonID);
        """)

    print('Protein_table table successfully created!')


    # ---------------------
    # Member Table generation
    # ----------------------
    members = pd.read_csv(data_path + "vog.members.tsv.gz", compression='gzip',
                          sep='\t',
                          header=0,
                          names=['VOG_ID', 'ProteinCount', 'SpeciesCount', 'FunctionalCategory', 'Proteins'],
                          usecols=['VOG_ID', 'ProteinCount', 'SpeciesCount', 'FunctionalCategory', 'Proteins'],
                          index_col='VOG_ID').assign(Proteins=lambda df: df.Proteins.apply(lambda s: set(s.split(","))))

    # ASSIGNING MEMBERSHIP:
    def extract_membership(members):
        """
        Loads all vog<->protein relationships.
        :param members data frame
        """
        data = [(v, p) for v, ps in members.Proteins.items() for p in ps]
        return (
            pd.DataFrame.from_records(data, columns=["VOG_ID", "ProteinID"])
                .sort_values(["VOG_ID", "ProteinID"])
                .reset_index(drop=True)
        )

    membership = extract_membership(members)

    membership.to_sql(
        name="Member",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={"VOG_ID": String(30), "ProteinID": String(30)},
    )

    with engine.connect() as con:
        con.execute(
            """
        ALTER TABLE Member  
            MODIFY VOG_ID varchar(30) NOT NULL,
            MODIFY ProteinID varchar(30) NOT NULL,
            ADD PRIMARY KEY(VOG_ID, ProteinID),
            ADD FOREIGN KEY(VOG_ID) REFERENCES VOG_table(VOG_ID),
            ADD FOREIGN KEY(ProteinID) REFERENCES Protein_table(ProteinID);
        """
        )

    print("Member table created!")

    # ---------------------
    # VOG_table generation
    # ----------------------

    annotations = pd.read_csv(data_path + "vog.annotations.tsv.gz", compression='gzip',
                              sep='\t',
                              header=0,
                              names=['VOG_ID', 'ProteinCount', 'SpeciesCount', 'FunctionalCategory', 'Consensus_func_description'],
                              usecols=['VOG_ID', 'Consensus_func_description'],
                              index_col='VOG_ID')

    #lca = pd.read_csv(os.path.join(data_path, 'vog.lca.tsv.gz'), compression='gzip',
    lca = pd.read_csv(data_path + 'vog.lca.tsv.gz', compression='gzip',
                      sep='\t',
                      header=0,
                      names=['VOG_ID', 'GenomesInGroup', 'GenomesTotal', 'Ancestors'],
                      index_col='VOG_ID')

    virusonly = pd.read_csv(data_path + 'vog.virusonly.tsv.gz', compression='gzip',
                            sep='\t',
                            header=0,
                            names=['VOG_ID', 'StringencyHigh', 'StringencyMedium', 'StringencyLow'],
                            dtype={'StringencyHigh': bool, 'StringencyMedium': bool, 'StringencyLow': bool},
                            index_col='VOG_ID')

    dfr = members.join(annotations).join(lca).join(virusonly)
    dfr['VirusSpecific'] = np.where((dfr['StringencyHigh'] | dfr['StringencyMedium'] | dfr['StringencyLow']), True, False)


    #create num of phages and non-phages for VOG. also "phages_only" "np_only" or "mixed"
    dfr['NumPhages'] = 0
    dfr['NumNonPhages'] = 0
    dfr['PhageNonphage'] = ''

    species_list_df.set_index("TaxonID", inplace=True)
    for index, row in dfr.iterrows():
        num_nonphage = 0
        num_phage = 0
        p = row['Proteins'].split(",")
        for protein in p:
            species_id = protein.split('.')[0]
            species_id = int(species_id)
            if (species_list_df.loc[species_id])["Phage"]:
                num_phage = num_phage + 1
            else:
                num_nonphage = num_nonphage + 1

        dfr.at[index, 'NumPhages'] = num_phage
        dfr.at[index, 'NumNonPhages'] = num_nonphage

        if ((num_phage > 0) and (num_nonphage > 0)):
            dfr.at[index, 'PhageNonphage'] = "mixed"
        elif (num_phage > 0):
            dfr.at[index, 'PhageNonphage'] = "phages_only"
        else:
            dfr.at[index, 'PhageNonphage'] = "np_only"

    # Handled via relationship
    dfr = dfr.drop(columns="Proteins")

    # create a table in the database
    dfr.to_sql(name='VOG_table', con=engine, if_exists='replace', index=True, chunksize=1000, dtype={
        'VOG_ID': String(30),
        'FunctionalCategory': String(30),
        'Consensus_func_description': String(100),
        'ProteinCount': Integer,
        'SpeciesCount': Integer,
        'GenomesInGroup': Integer,
        'GenomesTotal': Integer,
        'Ancestors': String(255),
        'StringencyHigh': Boolean,
        'StringencyMedium': Boolean,
        'StringencyLow': Boolean,
        'VirusSpecific': Boolean,
        'NumPhages': Integer,
        'NumNonPhages': Integer,
        'PhageNonphage': String(32)
        })

    with engine.connect() as con:
        con.execute("""
        ALTER TABLE VOG_table
            MODIFY VOG_ID varchar(30) NOT NULL PRIMARY KEY,
            MODIFY FunctionalCategory varchar(30) NOT NULL,
            MODIFY Consensus_func_description varchar(100) NOT NULL,
            MODIFY ProteinCount int NOT NULL,
            MODIFY SpeciesCount int NOT NULL,
            MODIFY GenomesInGroup int NOT NULL,
            MODIFY GenomesTotal int NOT NULL,
            MODIFY Ancestors varchar(255) NULL,
            MODIFY StringencyHigh bool NOT NULL,
            MODIFY StringencyMedium bool NOT NULL,
            MODIFY StringencyLow bool NOT NULL,
            MODIFY VirusSpecific bool NOT NULL,
            MODIFY NumPhages int NOT NULL,
            MODIFY NumNonPhages int NOT NULL,
            MODIFY PhageNonphage varchar(32) NOT NULL;
        """)

    print('VOG_table successfully created!')


    with engine.connect() as con:
        con.execute("OPTIMIZE LOCAL TABLE Species_table, VOG__table, Protein_table, Mapping;")

    print("All tables optimized!")


    #
    # #---------------------
    # # Table_mapping generation
    # #----------------------
    #
    # # extract proteins for each VOG
    # protein_list_df = pd.read_csv(data_path + "vog.members.tsv.gz", compression='gzip', sep='\t').iloc[:, [0, 4]]
    #
    # protein_list_df = protein_list_df.rename(columns={"#GroupName": "VOG_ID", "ProteinIDs": "ProteinID"})
    #
    # # assign each protein a vog
    # protein_list_df = (protein_list_df["ProteinID"].str.split(",").apply(lambda x: pd.Series(x))
    #                    .stack()
    #                    .reset_index(level=1, drop=True)
    #                    .to_frame("ProteinID")
    #                    .join(protein_list_df[["VOG_ID"]], how="left")
    #                    )
    # protein_list_df.set_index("ProteinID")
    #
    # # separate protein and taxonID into separate columns
    # protein_list_df["TaxonID"] = protein_list_df["ProteinID"].str.split(".").str[0]
    #
    # # create a protein table in the database
    # protein_list_df.to_sql(name='Table_mapping', con=engine, if_exists='replace', index=False, chunksize=1000, dtype={
    #     'ProteinID': String(30),
    #     'VOG_ID': String(30),
    #     'TaxonID': Integer
    # })
    #
    # with engine.connect() as con:
    #     con.execute("""
    #     ALTER TABLE Table_mapping
    #         MODIFY ProteinID varchar(30) NOT NULL,
    #         MODIFY VOG_ID varchar(30) NOT NULL,
    #         ADD PRIMARY KEY(VOG_ID, ProteinID),
    #         ADD FOREIGN KEY(VOG_ID) REFERENCES VOG_profile(VOG_ID),
    #         ADD FOREIGN KEY(ProteinID) REFERENCES Protein_profile(ProteinID);
    #         ADD INDEX(VOG_ID),
    #         ADD INDEX(ProteinID);
    #     """)
    #
    # print('Table_mapping table successfully created!')


    #
    # #---------------------
    # # Amino Acid and Nucleotide Sequence Table Generation
    # #----------------------
    #
    # proteinfile = data_path + "vog.proteins.all.fa"
    # prot = []
    # for seq_record in SeqIO.parse(proteinfile, "fasta"):
    #     prot.append([seq_record.id, str(seq_record.seq)])
    # df = pd.DataFrame(prot, columns=['ID', 'AAseq'])
    # df.set_index("ID")
    #
    # # convert dataframe to DB Table:
    # df.to_sql(name='AA_seq', con=engine, if_exists='replace', index=False, chunksize=1000, dtype={
    #     'ID': String(30),
    #     'AAseq': Text(65000)
    # })
    #
    # with engine.connect() as con:
    #     con.execute("""
    #     ALTER TABLE AA_seq
    #         MODIFY ID varchar(30) NOT NULL PRIMARY KEY,
    #         MODIFY AAseq text NOT NULL;
    #     """)
    #
    # print('Amino-acid sequences table successfully created!')
    #
    #
    # genefile = data_path + "vog.genes.all.fa"
    # genes = []
    # for seq_record in SeqIO.parse(genefile, "fasta"):
    #     genes.append([seq_record.id, str(seq_record.seq)])
    # dfg = pd.DataFrame(genes, columns=['ID', 'NTseq'])
    # dfg.set_index('ID')
    #
    # # convert dataframe to DB table:
    # dfg.to_sql(name='NT_seq', con=engine, if_exists='replace', index=False, chunksize=1000, dtype={
    #     'ID': String(30),
    #     'NTseq': Text(65000)
    # })
    #
    # with engine.connect() as con:
    #     con.execute("""
    #     ALTER TABLE NT_seq
    #         MODIFY ID varchar(30) NOT NULL PRIMARY KEY,
    #         MODIFY NTseq mediumtext NOT NULL;
    #     """)
    #
    # print('Nucleotide sequences table successfully created!')
