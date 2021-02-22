from pydantic import BaseModel, Field
from typing import Optional, Set, List

"""
 Here we define the "schemas" i.e. specify what the output response should look like (which columns to select)
"""

"""
Very important Note: Here we specify what columns we want to return to the client
Pydantic models bridges with SQLAlchemy models.
In order that we connect Pydantic with SQLAlchemy, two criteria need to be valid:
1. the attribute type values of the returned query object (in functionality.py)  (e.g. Species_profile.species_name)
 need to match the attribute type of the Pydantic response model (in this case schemas.Species_profile.species_name)
2. The names of the  attributes the returned query object also need to be exactly the same as in the Pydantic 
response model object, so we have in query object with attribute Protein_profile.species_name
so the pydantic response model (Protein_profile) needs to have the attribute name species_name as well

if those two criteria are not fulfilled, pydantic will throw an ValidationError
"""

class WELCOME(BaseModel):
    message: str = Field(..., example="Hello!")
    version: int = Field(..., example=202)

    class Config:
        orm_mode = True


class VOG_UID(BaseModel):
    id: str = Field(..., example="VOG00001")

    class Config:
        orm_mode = True


class Species_ID(BaseModel):
    taxon_id: int = Field(..., example=11128)

    class Config:
        orm_mode = True


class ProteinID(BaseModel):
    id: str = Field(..., example="1048207.YP_009018659.1")

    class Config:
        orm_mode = True


class VOG_base(VOG_UID):
    protein_count: int = Field(..., example=10)
    species_count: int = Field(..., example=10)
    function: str = Field(..., example="Xu")
    consensus_function: str = Field(..., example="Excisionase")
    genomes_in_group: int = Field(..., example=10)
    genomes_total_in_LCA: int = Field(..., example=10)
    ancestors: str = Field(..., example="Viruses")
    h_stringency: bool = Field(..., example=True)
    m_stringency: bool = Field(..., example=True)
    l_stringency: bool = Field(..., example=True)

    class Config:
        orm_mode = True


class VOG_profile(VOG_base):
    proteins: List[ProteinID]

    class Config:
        orm_mode = True


class Species_base(Species_ID):
    species_name: str = Field(..., example="Bovine coronavirus")
    phage: bool = Field(..., example=True)
    source: str = Field(..., example="NCBI Refseq")
    version: int = Field(..., example=202)

    class Config:
        orm_mode = True


class Species_profile(Species_base):
    proteins: List[ProteinID]

    class Config:
        orm_mode = True


class Protein_profile(ProteinID):
    # aa_seq: str
    # nt_seq: str
    vogs: List[VOG_base]
    species: Species_base

    class Config:
        orm_mode = True


class AA_seq(ProteinID):
    aa_seq: str = Field(..., example="MTNAIRVRTDRMKNLTEIHGLNESETARRIGCSRQTYRRAIDGENVSAGFVAGACLSFGVPFDALFHTVRVEAETPAA")

    class Config:
        orm_mode = True


class NT_seq(ProteinID):
    nt_seq: str = Field(..., example="ATGACCAACGCGATCAGGGTCCGCACGGACCGCATGAAGAACTTGACGGAAATCCACGGACTGAACGAGTCCGAGACT")

    class Config:
        orm_mode = True
