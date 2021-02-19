import os
import random
import string
import time

import pytest
from fastapi.testclient import TestClient
import pandas as pd
from six import assertCountEqual

from vogdb.main import api
from httpx import AsyncClient

""" Tests for vogdb.main.py
Test naming convention
test_MethodName_ExpectedBehavior_StateUnderTest:
e.g. test_isAdult_False_AgeLessThan18

test prefix is important for in order for the pytest to recognize it as test function. 
If there is no "test" prefix, pytest will not execute this test function.
"""


@pytest.fixture(scope="session")
def get_test_client():
    return TestClient(api)



@pytest.mark.vogapi
def test_defaultEndpoint_version202_get(get_test_client):
    client = get_test_client
    response = client.get(url="/")
    assert response.json().get("version") == 202, "DB version for testing has to be 202."

@pytest.fixture(scope="session")
def get_test_asynclient():
    client = AsyncClient(app=api, base_url="http://127.0.0.1:8001")
    return client

@pytest.fixture(autouse=True)
def teardown():
    time.sleep(0.1)

#------------------------
# vSummary/vog tests
#------------------------
@pytest.mark.vsummary_vog
def test_vsummaryVog_vogProfiles_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00002", "VOG00234", "VOG03456"]}
    response = client.get(url="/vsummary/vog/", params=params)
    expected = ["VOG00001", "VOG00002", "VOG00234", "VOG03456"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate

    assert data["id"].to_list() == expected

@pytest.mark.vsummary_vog
def test_vsummaryVog_vogProfileFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00002", "VOG00234", "VOG03456"]}
    response = client.get(url="/vsummary/vog/", params=params)
    expected = ['id', 'protein_count', 'species_count', 'function',
       'consensus_function', 'genomes_in_group', 'genomes_total_in_LCA',
       'ancestors', 'h_stringency', 'm_stringency', 'l_stringency',
       'proteins']

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    assert list(data.keys()) == expected

@pytest.mark.vsummary_vog
@pytest.mark.parametrize("key, expected", [("id", str), ('protein_count', int), ('species_count', int), ('function', str),
                                           ('consensus_function', str), ('genomes_in_group', int),('genomes_total_in_LCA', int),
                                           ('ancestors', str), ('h_stringency', bool), ('m_stringency', bool),( 'l_stringency', bool),
                                           ('proteins', list)])
def test_vsummaryVog_vogProfileFieldTypes_ids(key, expected, get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001"]}
    response = client.get(url="/vsummary/vog/", params=params)

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    element = data[key].to_list()[0]
    assert type(element) is expected

@pytest.mark.vsummary_vog
def test_vsummaryVog_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00002", "VOG00234", "VOG03456"]}

    response = client.get(url="/vsummary/vog/", params=params)
    expected_response = client.get(url="/vsummary/vog/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert response_data == expected_data

@pytest.mark.vsummary_vog
def test_vsummaryVog_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00002", "VOG00234", "VOG03456"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsummary/vog/", params=params)
    end = time.time()

    assert end-start <= expected_time

@pytest.mark.vsummary_vog
def test_vsummaryVog_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsummary/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_vog
def test_vsummaryVog_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vsummary/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_vog
def test_vsummaryVog_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vsummary/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_vog
def test_vsummaryVog_ERROR422_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vsummary/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_vog
@pytest.mark.asyncio
async def test_vsummaryVog_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["VOG00001"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsummary/vog/", params=params)
        response = await client.get(url="/vsummary/vog/", params=params)

    expected = 429
    assert response.status_code == expected


#------------------------
# vSummary/species
#------------------------

@pytest.mark.vsummary_species
def test_vsummarySpecies_SpeciesProfilesTaxonIDs_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["2713301", "2713308"]}
    response = client.get(url="/vsummary/species/", params=params)
    expected = [2713301, 2713308]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate

    assert data["taxon_id"].to_list() == expected

@pytest.mark.vsummary_species
def test_vsummarySpecies_speciesProfileFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["2713301", "2713308"]}
    response = client.get(url="/vsummary/species/", params=params)
    expected = ['taxon_id', 'species_name', 'phage', 'source','version', 'proteins']

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    assert list(data.keys()) == expected

@pytest.mark.vsummary_species
@pytest.mark.parametrize("key, expected", [("taxon_id", int), ('species_name', str), ('phage', str), ('source', str), #ToDo phage should be boolean
                                           ('version', int), ('proteins', list)])
def test_vsummarySpecies_speciesProfileFieldTypes_ids(key, expected, get_test_client):
    client = get_test_client
    params = {"taxon_id": ["2713301"]}
    response = client.get(url="/vsummary/species/", params=params)

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    element = data[key].to_list()[0]

    assert type(element) is expected

@pytest.mark.vsummary_species
def test_vsummarySpecies_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["2713301", "2713308"]}

    response = client.get(url="/vsummary/species/", params=params)
    expected_response = client.get(url="/vsummary/species/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert response_data == expected_data

@pytest.mark.vsummary_species
def test_vsummarySpecies_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["2713301", "2713308"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsummary/species/", params=params)
    end = time.time()

    assert end-start <= expected_time

@pytest.mark.vsummary_species
def test_vsummarySpecies_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["SOMETHING"]}
    response = client.get(url="/vsummary/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_species
def test_vsummarySpecies_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"taxon_id": None}
    response = client.get(url="/vsummary/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_species
def test_vsummarySpecies_ERROR422_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"taxon_id": long_string }
    response = client.get(url="/vsummary/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_species
@pytest.mark.asyncio
async def test_vsummarySpecie_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"taxon_id": ["2713301"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsummary/species/", params=params)
        response = await client.get(url="/vsummary/species/", params=params)

    expected = 429
    assert response.status_code == expected



#------------------------
# vSummary/protein
#------------------------

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ProteinProfiles_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = ["11128.NP_150082.1", "2301601.YP_009812740.1"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate

    assert data["id"].to_list() == expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_proteinProfileFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = ['id', 'vogs', 'species']

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    assert list(data.keys()) == expected

@pytest.mark.vsummary_protein
@pytest.mark.parametrize("key, expected", [("id", str), ('vogs', list), ('species', dict)])
def test_vsummarySpecies_speciesProfileFieldTypes_ids(key, expected, get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1"]}
    response = client.get(url="/vsummary/protein/", params=params)

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    element = data[key].to_list()[0]

    assert type(element) is expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    response = client.get(url="/vsummary/protein/", params=params)
    expected_response = client.get(url="/vsummary/protein/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert response_data == expected_data

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsummary/protein/", params=params)
    end = time.time()

    assert end-start <= expected_time

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ERROR422_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vsummary/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_protein
def test_vsummaryProtein_ERROR422_validAndInvalid(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING", "11128.NP_150082.1"]}
    response = client.get(url="/vsummary/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsummary_species
@pytest.mark.asyncio
async def test_vsummaryProtein_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["11128.NP_150082.1"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsummary/protein/", params=params)
        response = await client.get(url="/vsummary/protein/", params=params)


    expected = 429
    assert response.status_code == expected




#------------------------
# vfetch/vog
#------------------------

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_HMMProfilesKeysAreVOGID_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = ["VOG00234", "VOG00003"]

    response_data = response.json()
    data = list(response_data.keys())

    assert sorted(data) == sorted(expected)



@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_HMMProfileAsDict_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = type(dict())

    data = response.json()
    assert type(data) == expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_HMMProfileContainsHMM_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 100

    data = response.json()
    hmms_len = len(list(data.values())[0])
    assert hmms_len >= expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}

    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected_response = client.get(url="/vfetch/vog/hmm/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert sorted(list(response_data.keys())) == sorted(list(expected_data.keys()))
    assert sorted(list(response_data.values())) == sorted(list(expected_data.values()))

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM__ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    end = time.time()

    response_time = end-start
    assert response_time <= expected_time


@pytest.mark.vfetch_hmm
@pytest.mark.asyncio
async def test_vfetch_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["VOG00002"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vfetch/vog/hmm/", params=params)

        response = await client.get(url="/vfetch/vog/hmm/", params=params)

    expected = 429
    assert response.status_code == expected


@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [123132]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR404_invalidVOG(get_test_client):
    client = get_test_client
    params = {"id": ["VOG0999999"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 404

    assert response.status_code == expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR404_ValidVOGandInvalidVOG(get_test_client):
    client = get_test_client
    params = {"id": ["VOG0999999", "VOG00001"]}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vfetch_hmm
def test_vfetchVogHMM_ERROR22_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vfetch/vog/hmm/", params=params)
    expected = 422

    assert response.status_code == expected


#------------------------
# vfetch/msa
#------------------------

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_MSAProfilesKeysAreVOGID_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = ["VOG00234", "VOG00003"]

    response_data = response.json()
    data = list(response_data.keys())

    assert sorted(data) == sorted(expected)



@pytest.mark.vfetch_msa
def test_vfetchVogMSA_MSAProfileAsDict_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = type(dict())

    data = response.json()
    assert type(data) == expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_MSAProfileContainsHMM_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 100

    data = response.json()
    hmms_len = len(list(data.values())[0])
    assert hmms_len >= expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}

    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected_response = client.get(url="/vfetch/vog/msa/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert sorted(list(response_data.keys())) == sorted(list(expected_data.keys()))
    assert sorted(list(response_data.values())) == sorted(list(expected_data.values()))

@pytest.mark.vfetch_msa
def test_vfetchVogMSA__ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00234", "VOG00003"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vfetch/vog/msa/", params=params)
    end = time.time()

    response_time = end-start
    assert response_time <= expected_time


@pytest.mark.vfetch_msa
@pytest.mark.asyncio
async def test_vfetchMSA_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["VOG00002"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vfetch/vog/msa/", params=params)
        response = await client.get(url="/vfetch/vog/msa/", params=params)

    expected = 429
    assert response.status_code == expected


@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [123132]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR404_invalidVOG(get_test_client):
    client = get_test_client
    params = {"id": ["VOG0999999"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 404

    assert response.status_code == expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR200_invalidAndValidVOG (get_test_client):
    client = get_test_client
    params = {"id": ["VOG0999999", "VOG00001"]}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vfetch_msa
def test_vfetchVogMSA_ERROR22_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vfetch/vog/msa/", params=params)
    expected = 422

    assert response.status_code == expected


#------------------------
# vfetch/protein/faa
#------------------------

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_FAAProfiles_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected =["11128.NP_150082.1", "2301601.YP_009812740.1"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate

    assert data["id"].to_list() == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_FAAProfiles_InvalidID(get_test_client):
    client = get_test_client
    params = {"id": ["3016123101.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 404

    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_FAAProfiles_ValidAndInvalidID(get_test_client):
    client = get_test_client
    params = {"id": ["3016123101.YP_009812740.1", "11128.NP_150082.1"]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_FAAFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = ["id", "aa_seq"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    assert list(data.keys()) == expected




@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected_response = client.get(url="/vfetch/protein/faa/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert response_data == expected_data

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vfetch/protein/faa/", params=params)
    end = time.time()

    response_time = end-start
    assert response_time <= expected_time


@pytest.mark.vfetch_protein_faa
@pytest.mark.asyncio
async def test_vfetchProteinFAA_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["11128.NP_150082.1"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vfetch/protein/faa/", params=params)
        response = await client.get(url="/vfetch/protein/faa/", params=params)

    expected = 429
    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [123132]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_faa
def test_vfetchProteinFAA_ERROR422_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vfetch/protein/faa/", params=params)
    expected = 422

    assert response.status_code == expected





#------------------------
# vfetch/protein/fna
#------------------------

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_FAAProfiles_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected =["11128.NP_150082.1", "2301601.YP_009812740.1"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate

    assert data["id"].to_list() == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_FAAProfiles_InvalidID(get_test_client):
    client = get_test_client
    params = {"id": ["3016123101.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 404

    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_FAAProfiles_ValidAndInvalidID(get_test_client):
    client = get_test_client
    params = {"id": ["3016123101.YP_009812740.1", "11128.NP_150082.1"]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_FAAFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = ["id", "nt_seq"]

    data = response.json()
    data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    assert list(data.keys()) == expected


@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected_response = client.get(url="/vfetch/protein/fna/", params=params)

    response_data = response.json()
    expected_data = expected_response.json()

    assert response_data == expected_data

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["11128.NP_150082.1", "2301601.YP_009812740.1"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vfetch/protein/fna/", params=params)
    end = time.time()

    response_time = end-start
    assert response_time <= expected_time


@pytest.mark.vfetch_protein_fna
@pytest.mark.asyncio
async def test_vfetchProteinFNA_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["11128.NP_150082.1"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vfetch/protein/fna/", params=params)
        response = await client.get(url="/vfetch/protein/fna/", params=params)

    expected = 429
    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_ERROR422_integers(get_test_client):
    client = get_test_client
    params = {"id": [123132]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_ERROR422_randomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_ERROR422_noParameter(get_test_client):
    client = get_test_client
    params = {"id": None}
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vfetch_protein_fna
def test_vfetchProteinFNA_ERROR422_longParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vfetch/protein/fna/", params=params)
    expected = 422

    assert response.status_code == expected




#------------------------
# vSearch/protein
#------------------------

@pytest.mark.vsearch_protein
def test_vsearchProtein_ProteinProfilesTaxonIDs_TaxonIds(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = ["10295", "10298"]

    data = response.text.split("\n")

    # we check if every response id contains any expected va
    # we check of the return values are correct, but actually do not check if all taxon ids have been found
    for response_id in data:
        assert any(expected_val in response_id for expected_val in expected)

@pytest.mark.vsearch_protein
def test_vsearchProtein_ProteinProfilesTaxonIDs_SpeciesIdAndTaxonId(get_test_client):
    client = get_test_client
    params = {"species_name": ["herpes"], "taxon_id": "10310"}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = ["10310"]

    data = response.text.split("\n")
    for response_id in data:
        assert expected[0] in response_id

@pytest.mark.vsearch_protein
def test_vsearchProtein_ProteinProfiles_SpeciesIdAndTaxonIdAndVOGId(get_test_client):
    client = get_test_client
    params = {"species_name": ["lacto"], "taxon_id": "37105", "VOG_id":["VOG00001"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = ["37105"]

    data = response.text.split("\n")
    for response_id in data:
        assert expected[0] in response_id

@pytest.mark.vsearch_protein
def test_vsearchProtein_proteinProfileResponseType_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = str

    data = response.text.split("\n")
    assert type(data[0]) == expected


@pytest.mark.vsearch_protein
def test_vsearchProtein_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}

    response = client.get(url="/vsearch/protein/", params=params)
    expected_response = client.get(url="/vsearch/protein/", params=params)

    response_data = response.text.split("\n")
    expected_data = response.text.split("\n")

    assert response_data == expected_data

@pytest.mark.vsearch_protein
def test_vsearchProtein_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsearch/protein/", params=params)
    end = time.time()

    assert end-start <= expected_time


@pytest.mark.vsearch_protein
@pytest.mark.asyncio
async def test_vsearchProtein_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"taxon_id": ["10295"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsearch/protein/", params=params)
        response = await client.get(url="/vsearch/protein/", params=params)

    expected = 429
    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_MadeUpTaxonID(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["1231", "123", "124124", "1123"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_taxonIDrandomString(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["SOMETHING"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR400_taxonIDnoParameter(get_test_client):
    client = get_test_client
    params = {"taxon_id": None}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_taxonIDlongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"taxon_id": long_string }
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_speciesNameIntegers(get_test_client):
    client = get_test_client
    params = {"species_name": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_speciesNamerandomString(get_test_client):
    client = get_test_client
    params = {"species_name": ["SOMETHING"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 200
    # expected = []
    # data = response.json()
    # data = pd.DataFrame.from_dict(data) # converting to df so its easier to validate
    # assert data["id"].to_list() == expected

    assert response.status_code == expected


@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR400_speciesNamenoParameter(get_test_client):
    client = get_test_client
    params = {"species_name": None}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_speciesNamelongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"species_name": long_string }
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_VOGIDIntegers(get_test_client):
    client = get_test_client
    params = {"VOG_id": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_VOGIDrandomString(get_test_client):
    client = get_test_client
    params = {"VOG_id": ["SOMETHING"]}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR400_VOGIDnoParameter(get_test_client):
    client = get_test_client
    params = {"VOG_id": None}
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_protein
def test_vsearchProtein_ERROR422_VOGIDlongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"VOG_id": long_string }
    response = client.get(url="/vsearch/protein/", params=params)
    expected = 422

    assert response.status_code == expected




#------------------------
# vSearch/species
#------------------------

# taxon_id is a integer and it should be a string
@pytest.mark.vsearch_species
def test_vsearchSpecies_SpeciesProfiles_Ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["11128", "1335626", "1384461"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = ["11128", "1335626", "1384461"]

    data = response.text.split("\n")

    for response_id in data:
        assert any(expected_val in response_id for expected_val in expected)


@pytest.mark.vsearch_species
def test_vsearchSpecies_TaxonIDs_AllParameters(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["12390", "12348", "1384461"],
              "name": "lacto",
              "phage": True,
              "source": "NCBI Refseq"}
    response = client.get(url="/vsearch/species/", params=params)
    expected = ["12390", "12348"]

    data = response.text.split("\n")

    for response_id in data:
        assert any(expected_val in response_id for expected_val in expected)


@pytest.mark.vsearch_species
def test_vsearchSpecies_proteinSpeciesFieldType_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = str

    data = response.text.split("\n")

    assert type(data[0]) == expected

@pytest.mark.vsearch_species
@pytest.mark.asyncio
async def test_vsearchSpecies_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"taxon_id": ["10295"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsearch/species/", params=params)
        response = await client.get(url="/vsearch/species/", params=params)

    expected = 429
    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}

    response = client.get(url="/vsearch/species/", params=params)
    expected_response = client.get(url="/vsearch/species/", params=params)

    response_data = response.text.split("\n")

    expected_data = response.text.split("\n")

    assert response_data == expected_data

@pytest.mark.vsearch_species
def test_vsearchSpecies_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["10295", "10298"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsearch/species/", params=params)
    end = time.time()

    assert end-start <= expected_time



@pytest.mark.vsearch_species
def test_vsearchSpecies_MadeUpTaxonIDs(get_test_client):
    client = get_test_client
    params = {"taxon_id": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_idsRandomString(get_test_client):
    client = get_test_client
    params = {"taxon_id": ["SOMETHING"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpeciesERROR400_idsNoParameter(get_test_client):
    client = get_test_client
    params = {"taxon_id": None}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 400

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_IdsLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"taxon_id": long_string }
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_nameIntegers(get_test_client):
    client = get_test_client
    params = {"name": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpecies_nameRandomString(get_test_client):
    client = get_test_client
    params = {"name": ["SOMETHING"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpeciesERROR400_nameNoParameter(get_test_client):
    client = get_test_client
    params = {"name": None}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_nameLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"name": long_string }
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_phageIntegers(get_test_client):
    client = get_test_client
    params = {"phage": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_phageRandomString(get_test_client):
    client = get_test_client
    params = {"phage": ["SOMETHING"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpeciesERROR400_phageNoParameter(get_test_client):
    client = get_test_client
    params = {"phage": None}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 400

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_phageLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"phage": long_string }
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_sourceIntegers(get_test_client):
    client = get_test_client
    params = {"source": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_sourceRandomString(get_test_client):
    client = get_test_client
    params = {"source": ["SOMETHING"]}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 200

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpeciesERROR400_sourceNoParameter(get_test_client):
    client = get_test_client
    params = {"source": None}
    response = client.get(url="/vsearch/species/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_species
def test_vsearchSpecies_ERROR422_sourceLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"source": long_string }
    response = client.get(url="/vsearch/species/", params=params)
    expected = 422

    assert response.status_code == expected



#------------------------
# vSearch/vog
#------------------------
@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIds_VOGIds(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00023", "VOG00234"], "inclusive": "i"}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ["VOG00001", "VOG00023", "VOG00234"]

    data = response.text.split("\n")
    assert data == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_AllParameters(get_test_client):
    client = get_test_client
    params = {"union": False,
              "pmin": 1,
              "pmax": 100,
              "smax": 500,
              "smin": 1,
              "functional_category": "XrXs",
              "consensus_function": None,
              "mingLCA": 4,
              "maxGLCA": 100,
              "mingGLCA":5,
              "maxgGLCA":5000,
              "ancestors": None,
              "h_stringency": False ,
              "m_stringency": False,
              "l_stringenca": True,
              "virus_specific": True,
              "phages_nonphages":"phages_only",
              "proteins": None,
              "species": None,
              "tax_id": None}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ["VOG01269", "VOG05997", "VOG07355"]

    data = response.text.split("\n")
    assert data == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGProfileFieldNames_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00023", "VOG00234"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = str

    data = response.text.split("\n")
    assert type(data[0]) == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_isIdempotent_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00023", "VOG00234"]}

    response = client.get(url="/vsearch/vog/", params=params)
    expected_response = client.get(url="/vsearch/vog/", params=params)

    response_data = response.text.split("\n")
    expected_data = expected_response.text.split("\n")

    assert response_data == expected_data

@pytest.mark.vsearch_vog
def test_vsearchVOG_ResponseUnder500ms_ids(get_test_client):
    client = get_test_client
    params = {"id": ["VOG00001", "VOG00023", "VOG00234"]}

    expected_time = 0.5
    start = time.time()
    response = client.get(url="/vsearch/vog/", params=params)
    end = time.time()

    assert end-start <= expected_time


@pytest.mark.vsearch_vog
@pytest.mark.asyncio
async def test_vsearchSpecies_ERROR429_11requestsPerSecond(get_test_asynclient):
    client = get_test_asynclient
    params = {"id": ["VOG00001"]}

    async with client:
        for _ in range(11):
            await client.get(url="/vsearch/vog/", params=params)
        response = await client.get(url="/vsearch/vog/", params=params)

    expected = 429
    assert response.status_code == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_idsIntegers(get_test_client):
    client = get_test_client
    params = {"id": [657567, 123, 124124, 1123]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_idsRandomString(get_test_client):
    client = get_test_client
    params = {"id": ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_IdsLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"id": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

# functional category
@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_functional_category(get_test_client):
    client = get_test_client
    params = {"functional_category": ["Xr"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = [ 'VOG01642', 'VOG01646', 'VOG01709', 'VOG01716', 'VOG01733', 'VOG01771', 'VOG01801', 'VOG01820',
                 'VOG01827', 'VOG01856', 'VOG01907', 'VOG01946', 'VOG01950', 'VOG01951', 'VOG01964', 'VOG02032',
                 'VOG02118', 'VOG02158', 'VOG02183', 'VOG02198', 'VOG02219']

    data = response.text.split("\n")

    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_unctional_categoryRandomString(get_test_client):
    client = get_test_client
    params = {"functional_category": ["AA"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_functional_categoryLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"functional_category": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_consensus_function(get_test_client):
    client = get_test_client
    params = {"consensus_function": ["Terminator"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG01051', 'VOG02143', 'VOG06859', 'VOG07559', 'VOG07655', 'VOG10010', 'VOG14228', 'VOG16905', 'VOG22337']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_consensus_functionRandomString(get_test_client):
    client = get_test_client
    params = {"consensus_function": ["123BAZ"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_consensus_functionLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"consensus_function": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_ancestors(get_test_client):
    client = get_test_client
    params = {"ancestors": ["Demosthenesvirus"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG15367', 'VOG15368', 'VOG15369', 'VOG15370', 'VOG15371', 'VOG15372', 'VOG15373', 'VOG15375',
                'VOG15377', 'VOG15378', 'VOG15379', 'VOG15380', 'VOG15381', 'VOG15382', 'VOG15383', 'VOG22440',
                'VOG22441', 'VOG22442', 'VOG22443', 'VOG22444']

    data = response.text.split("\n")

    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_ancestorsRandomString(get_test_client):
    client = get_test_client
    params = {"ancestors": ["123BAZ"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_ancestorsLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"ancestors": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_proteins(get_test_client):
    client = get_test_client
    params = {"proteins": ["1821555.YP_009603357.1"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG22444']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_proteinsRandomString(get_test_client):
    client = get_test_client
    params = {"proteins": ["YP"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_proteinsLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"proteins": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_phages_nonphages(get_test_client):
    client = get_test_client
    params = {"phages_nonphages": ["phages"], "function": ["XrXs"], "pmin": 500}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG00003', 'VOG00028', 'VOG00029', 'VOG00036', 'VOG00055', 'VOG00062', 'VOG00077', 'VOG00081',
                'VOG00088', 'VOG00101', 'VOG00134', 'VOG00136', 'VOG00354']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_phages_nonphagesRandomString(get_test_client):
    client = get_test_client
    params = {"phages_nonphages": ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_phages_nonphagesLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"phages_nonphages": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_species(get_test_client):
    client = get_test_client
    params = {"species": ["bovine coronavirus"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG03338', 'VOG05597', 'VOG05605', 'VOG05612', 'VOG05613', 'VOG05615', 'VOG05617', 'VOG05620',
                'VOG05621', 'VOG05622', 'VOG05623', 'VOG05624', 'VOG05627', 'VOG05632']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_speciesRandomString(get_test_client):
    client = get_test_client
    params = {"species": ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 200

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_phages_speciesLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"species": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_tax_id(get_test_client):
    client = get_test_client
    params = {"tax_id": ["1002725"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = ['VOG01680', 'VOG01723', 'VOG02058', 'VOG02083', 'VOG02174', 'VOG02256', 'VOG02257', 'VOG02290',
                'VOG02301', 'VOG02326', 'VOG02351', 'VOG02376', 'VOG02388', 'VOG02425', 'VOG02466', 'VOG02501',
                'VOG02511', 'VOG02598', 'VOG02601', 'VOG02603']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_tax_id_RandomString(get_test_client):
    client = get_test_client
    params = {"tax_id": ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)

    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR422_tax_idLongParameter(get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {"tax_id": long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

#pmin
@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_pmin(get_test_client):
    client = get_test_client
    params = {"pmin": [800]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")
    expected = ['VOG00001', 'VOG00028', 'VOG00029', 'VOG00036', 'VOG00077', 'VOG00088', 'VOG00103', 'VOG00220',
                'VOG00395', 'VOG00518', 'VOG00789', 'VOG00818', 'VOG01219', 'VOG01275', 'VOG02301', 'VOG05646',
                'VOG05658', 'VOG05707', 'VOG05727', 'VOG05902']
    assert data == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR404_pmaxOne(get_test_client):
    client = get_test_client
    params = {"pmax": 1}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")
    print(data)
    expected = 200
    assert response.status_code == expected

@pytest.mark.vsearch_vog
def test_vsearchVOG_ReturnsCorrectVOGs_pmaxTwo(get_test_client):
    client = get_test_client
    params = {"pmax": [2]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")

    expected = ['VOG26163', 'VOG26164', 'VOG26165', 'VOG26166', 'VOG26167', 'VOG26168', 'VOG26169', 'VOG26170',
                 'VOG26171', 'VOG26172', 'VOG26173', 'VOG26174', 'VOG26175', 'VOG26176', 'VOG26177']
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_smin(get_test_client):
    client = get_test_client
    params = {"smin": [200]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")

    expected = [ 'VOG00172', 'VOG00177', 'VOG00190', 'VOG00198', 'VOG00212', 'VOG00216', 'VOG00220', 'VOG00223',
                 'VOG00228', 'VOG00229', 'VOG00258', 'VOG00261', 'VOG00272', 'VOG00273', 'VOG00292', 'VOG00293',
                 'VOG00298', 'VOG00301', 'VOG00315', 'VOG00342', 'VOG00346', 'VOG00354', 'VOG00383', 'VOG00385',
                 'VOG00386', 'VOG00387', 'VOG00392', 'VOG00395', 'VOG00410']
    assert set(expected) <= set(data)


@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_smax(get_test_client):
    client = get_test_client
    params = {"smax": [2]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")
    expected = [ 'VOG25839', 'VOG25840', 'VOG25841', 'VOG25842', 'VOG25843', 'VOG25844', 'VOG25845', 'VOG25846',
                 'VOG25847', 'VOG25848', 'VOG25849', 'VOG25850', 'VOG25851', 'VOG25852', 'VOG25853']
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_mingLCA(get_test_client):
    client = get_test_client
    params = {"mingLCA": [5000]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")

    expected = [ 'VOG00447', 'VOG00452', 'VOG00475', 'VOG00501', 'VOG00505', 'VOG00518', 'VOG00521', 'VOG00535',
                 'VOG00554', 'VOG00557', 'VOG00561', 'VOG00609', 'VOG00638', 'VOG00643', 'VOG00651', 'VOG00665',
                 'VOG00697', 'VOG00720', 'VOG00749']
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_maxgLCA(get_test_client):
    client = get_test_client
    params = {"maxgLCA": [1]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")
    expected = ['VOG01967', 'VOG03740', 'VOG04300', 'VOG04344', 'VOG05242', 'VOG08486', 'VOG08487', 'VOG08488',
                'VOG12521']
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_mingGLCA(get_test_client):
    client = get_test_client
    params = {"mingGLCA": [2000]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")

    expected = ['VOG00818', 'VOG02301', 'VOG05658', 'VOG05707']
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_VOGIDs_maxgGLCA(get_test_client):
    client = get_test_client
    params = {"maxgGLCA": [1]}
    response = client.get(url="/vsearch/vog/", params=params)

    data = response.text.split("\n")
    print(data)
    expected = [ 'VOG14295', 'VOG14907', 'VOG14908', 'VOG14909', 'VOG14911', 'VOG18165', 'VOG18373', 'VOG18374',
                 'VOG18375', 'VOG18376', 'VOG18377']
    assert set(expected) <= set(data)


@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["pmin", "pmax", "smin", "smax", "maxgLCA", "mingLCA", "maxgGLCA", "mingGLCA"])
def test_vsearchVOG_ERROR422_pminNegative(key, get_test_client):
    client = get_test_client
    params = {key: [-657567]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["pmin", "pmax", "smin", "smax", "maxgLCA", "mingLCA", "maxgGLCA", "mingGLCA"])
def test_vsearchVOG_ERROR422_pminRandomString(key, get_test_client):
    client = get_test_client
    params = {key: ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected

@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["pmin", "pmax", "smin", "smax", "maxgLCA", "mingLCA", "maxgGLCA", "mingGLCA"])
def test_vsearchVOGERROR400_pminNoParameter(key, get_test_client):
    client = get_test_client
    params = {key: None}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["pmin", "pmax", "smin", "smax", "maxgLCA", "mingLCA", "maxgGLCA", "mingGLCA"])
def test_vsearchVOG_ERROR422_pminLongParameter(key, get_test_client):
    client = get_test_client
    letters = string.ascii_lowercase
    long_string = [''.join(random.choice(letters) for i in range(10000))]
    params = {key: long_string }
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["l_stringency", "m_stringency", "h_stringency", "union", "virus_specific"])
def test_vsearchVOG_ERROR422_string(key, get_test_client):
    client = get_test_client
    params = {key: ["SOMETHING"]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 422

    assert response.status_code == expected


@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["l_stringency", "m_stringency", "h_stringency", "union", "virus_specific"])
def test_vsearchVOG_ERROR400_empty(key, get_test_client):
    client = get_test_client
    params = {key: [None]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 400

    assert response.status_code == expected

@pytest.mark.vsearch_vog
@pytest.mark.parametrize("key", ["l_stringency", "m_stringency", "h_stringency"])
def test_vsearchVOG_ERROR422_booleanTrue(key, get_test_client):
    client = get_test_client
    params = {key: [True]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = [  'VOG07844', 'VOG07845', 'VOG07847', 'VOG07848', 'VOG07849', 'VOG07851', 'VOG07852', 'VOG07853',
                  'VOG07854', 'VOG07855', 'VOG07856', 'VOG07857', 'VOG07858', 'VOG07859', 'VOG07860', 'VOG07861',
                  'VOG07862', 'VOG07864', 'VOG07865', 'VOG07866', 'VOG07868']

    data = response.text.split("\n")
    assert set(expected) <= set(data)

@pytest.mark.vsearch_vog
def test_vsearchVOG_ERROR400_onlyUnionTrue(get_test_client):
    client = get_test_client
    params = {"union": [True]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = 400
    assert response.status_code == expected


@pytest.mark.vsearch_vog
def test_vsearchVOG_CorrectVOGs_UnionAndTaxonID(get_test_client):
    client = get_test_client
    params = {"union": [True], "tax_id": [320884, 10298]}
    response = client.get(url="/vsearch/vog/", params=params)
    expected = [ 'VOG04856', 'VOG04857', 'VOG04858', 'VOG04859', 'VOG04861', 'VOG04862', 'VOG04863', 'VOG04864',
                 'VOG04865', 'VOG04866', 'VOG04867']

    data = response.text.split("\n")
    assert  set(expected) <= set(data)





