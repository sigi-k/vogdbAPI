from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Boolean, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

"""
"model" refers to classes and instances that interact with the database.
A model is equivalent to a database table e.g. VOG_table and it contains all the same attributes
"""


class VOG_table(Base):
    __tablename__ = "VOG_table"

    id = Column('VOG_ID', String(30), primary_key=True)
    protein_count = Column('ProteinCount', Integer, nullable=False)
    species_count = Column('SpeciesCount', Integer, nullable=False)
    function = Column('FunctionalCategory', String(30), nullable=False)
    consensus_function = Column('Consensus_func_description', String(100), nullable=False)
    genomes_in_group = Column('GenomesInGroup', Integer, nullable=False)
    genomes_total_in_LCA = Column('GenomesTotal', Integer, nullable=False)
    ancestors = Column('Ancestors', String(255), nullable=True)
    h_stringency = Column('StringencyHigh', Boolean, nullable=False)
    m_stringency = Column('StringencyMedium', Boolean, nullable=False)
    l_stringency = Column('StringencyLow', Boolean, nullable=False)
    virus_specific = Column('VirusSpecific', Boolean, nullable=False)
    num_phages = Column('NumPhages', Integer, nullable=False)
    num_nonphages = Column('NumNonPhages', Integer, nullable=False)
    phages_nonphages = Column('PhageNonphage', String(32), nullable=False)

    proteins = relationship('Protein_table', secondary='Member', back_populates='vogs')
    members = relationship('Member', back_populates='vog', lazy='selectin')


class Species_table(Base):
    __tablename__ = "Species_table"

    taxon_id = Column('TaxonID', Integer, primary_key=True)
    species_name = Column('SpeciesName', String(100), nullable=False)
    phage = Column('Phage', Boolean, nullable=False)
    source = Column('Source', String(100), nullable=False)
    version = Column('Version', Integer, nullable=False)

    proteins = relationship("rotein_table", back_populates="species", lazy="selectin")


class Protein_table(Base):
    __tablename__ = "Protein_table"

    id = Column('ProteinID', String(30), nullable=False, index=True, primary_key=True)
    taxon_id = Column('TaxonID', Integer,  ForeignKey("Species_table.TaxonID"), nullable=False, index=True)
    aa_seq = Column('AASeq', String(65000), nullable=True)
    nt_seq = Column('NTSeq', String(65000), nullable=True)

    species = relationship("Species_table", back_populates="proteins", lazy="joined")
    vog = relationship('VOG_table', secondary='Member', back_populates='proteins')
    members = relationship('Member', back_populates='protein', lazy='selectin')


class Member(Base):
    __tablename__ = "Member"

    vog_id = Column('VOG_ID', String(30), ForeignKey('VOG_table.VOG_ID'), primary_key=True)
    protein_id = Column('ProteinID', String(30), ForeignKey('Protein_table.ProteinID'), primary_key=True)

    vog = relationship("VOG_table", back_populates="members", lazy="joined")
    protein = relationship("Protein_table", back_populates="members", lazy="joined")

