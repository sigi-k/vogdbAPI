#!/usr/bin/env python
# coding: utf-8

from ..database import database_url
from sqlalchemy import create_engine, MetaData, Table, func
import pandas as pd
from notify import notify


def count_rows():
    """Connect to MySQL VOGDB and count the number of rows in Tables vog, species and member."""

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

url = 'https://vogdb.csb.univie.ac.at/reports/release_stats'

def statistics():
    """Connect to vogdb release_stats
        Get the counts for species, proteins and vogs"""

    dfs = pd.read_html(url)
    species_web = int(dfs[1].iloc[2, 1])
    protein_web = int(dfs[2][1])
    vog_web = int(dfs[3].iloc[0, 1])
    return species_web, protein_web, vog_web


def compare():
    """Call the functions that count rows in VOGDB and that get the statistics from homepage.
    Compare the values.
    Send email notification if there is a discrepancy."""

    count_rows()
    statistics()
    try:
        print('Count the rows in MySQL VOGDB and compare with the statistics from VOG Homepage:')
        assert count_rows() == statistics()
    except AssertionError:
        print(f'The number of rows in the database does not correspond to the numbers given at {url}')
        notify()
        print('A notification was sent to CUBE IssueTracker.')
    else:
        print('The numbers of species, proteins and vogs in VOGDB are correct.')


if __name__ == '__main__':
    compare()