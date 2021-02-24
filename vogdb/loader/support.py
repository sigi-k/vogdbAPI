from sqlalchemy.types import Integer, String, Boolean, Text
from sqlalchemy import create_engine, MetaData, Table, select, func
import pandas as pd
import os
from database import database_url

"""
Here we create our VOGDB and create all the tables that we are going to use
"""


def save_db_sql(db_url, vog, species, proteins, membership):

    # Create an engine object.
    engine = create_engine(db_url)

    with engine.connect() as con:
        # V1 leftovers
        con.execute("DROP TABLE IF EXISTS NT_seq;")
        con.execute("DROP TABLE IF EXISTS AA_seq;")
        con.execute("DROP TABLE IF EXISTS Protein_profile;")
        con.execute("DROP TABLE IF EXISTS VOG_profile;")
        con.execute("DROP TABLE IF EXISTS Species_profile;")
        # V2
        con.execute("DROP TABLE IF EXISTS Member;")
        con.execute("DROP TABLE IF EXISTS Protein;")
        con.execute("DROP TABLE IF EXISTS VOG;")
        con.execute("DROP TABLE IF EXISTS Species;")

    # ---------------------
    # VOG_table generation
    # ----------------------

    # create a table in the database
    vog.reset_index().to_sql(
        name="VOG",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={
            "VOG_ID": String(30),
            "FunctionalCategory": String(30),
            "Consensus_func_description": String(100),
            "ProteinCount": Integer,
            "SpeciesCount": Integer,
            "GenomesInGroup": Integer,
            "GenomesTotal": Integer,
            "Ancestors": String(255),
            "StringencyHigh": Boolean,
            "StringencyMedium": Boolean,
            "StringencyLow": Boolean,
            "VirusSpecific": Boolean,
            "NumPhages": Integer,
            "NumNonPhages": Integer,
            "PhageNonphage": String(32),
        },
    )

    with engine.connect() as con:
        con.execute(
            """
        ALTER TABLE VOG
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
        """
        )

    print("VOG table created!")

    # ---------------------
    # Species generation
    # ----------------------

    species.reset_index().to_sql(
        name="Species",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={
            "TaxonId": Integer,
            "SpeciesName": String(100),
            "Phage": Boolean,
            "Source": String(100),
            "Version": Integer,
        },
    )

    with engine.connect() as con:
        con.execute(
            """
        ALTER TABLE Species
            MODIFY TaxonID int NOT NULL PRIMARY KEY,
            MODIFY SpeciesName varchar(100) NOT NULL,
            MODIFY Phage bool NOT NULL,
            MODIFY Source varchar(100) NOT NULL,
            MODIFY Version int NOT NULL;
        """
        )

    print("Species table created!")

    # ---------------------
    # Protein generation
    # ----------------------

    proteins.reset_index().to_sql(
        name="Protein",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={
            "ProteinID": String(30),
            "TaxonID": Integer,
            "AAseq": Text(65000),
            "NTseq": Text(65000),
        },
    )

    with engine.connect() as con:
        con.execute(
            """
        ALTER TABLE Protein
            MODIFY ProteinID varchar(30) NOT NULL PRIMARY KEY,
            MODIFY TaxonID int NOT NULL,
            MODIFY AAseq text NULL,
            MODIFY NTseq text NULL,
            ADD FOREIGN KEY(TaxonID) REFERENCES Species(TaxonID);
        """
        )

    print("Protein table created!")

    # ---------------------
    # Member generation
    # ----------------------

    membership.reset_index().to_sql(
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
            ADD FOREIGN KEY(VOG_ID) REFERENCES VOG(VOG_ID),
            ADD FOREIGN KEY(ProteinID) REFERENCES Protein(ProteinID);
        """
        )

    print("Member table created!")

    with engine.connect() as con:
        con.execute("OPTIMIZE LOCAL TABLE VOG, Species, Protein, Member;")

    print("All tables optimized!")


def db_rows():
    '''Connect to MySQL VOGDB and count the number of rows in Tables vog, species and member.'''

    engine = create_engine(database_url())
    metadata = MetaData()
    vog = Table('vog', metadata, autoload=True, autoload_with=engine)
    species = Table('Species', metadata, autoload=True, autoload_with=engine)
    member = Table('Member', metadata, autoload=True, autoload_with=engine)

    con = engine.connect()
    species_db = con.execute(func.count(species.columns.TaxonID)).scalar()
    protein_db = con.execute(func.count(member.columns.ProteinID)).scalar()
    vog_db = con.execute(func.count(vog.columns.VOG_ID)).scalar()
    return species_db, protein_db, vog_db


def file_rows():
    speciesfile = os.path.join(data_path, "vog.species.list")
    memberfile = os.path.join(data_path, "vog.members.tsv.gz")
    species = pd.read_csv(
        speciesfile,
        sep="\t",
        header=0)
    member = pd.read_csv(
        memberfile,
        compression="gzip",
        sep="\t",
        header=0)
    species_count = len(species.axes[0])
    protein_count = member.ProteinCount.sum()
    vog_count = len(member.axes[0])
    return species_count, protein_count, vog_count


def compare():
    '''Call the function that get row counts in VOGDB,
    call the function that get species, protein and vog counts in the flat files.
    Compare the values.
    '''
    print('Count the rows in MySQL VOGDB and compare with the statistics from VOG Homepage:')
    db_rows()
    file_rows()

    try:
        assert db_rows() == file_rows()
    except AssertionError:
        print(
            f'WARNING: The numbers of rows for species, proteins and vogs in the db {db_rows()} do not correspond to the numbers given in the files {file_rows()}')
        # notify()
        # print('A notification was sent to CUBE IssueTracker.')
    else:
        print(f'The numbers of species, proteins and vogs in VOGDB are correct {db_rows()}.')

