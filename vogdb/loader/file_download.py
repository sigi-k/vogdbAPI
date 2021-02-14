#!/usr/bin/env python
# coding: utf-8

from urllib.request import urlretrieve
import requests
import os
import pandas as pd
from hashlib import md5
from time import sleep
from notify import notify


url = 'http://fileshare.csb.univie.ac.at/vog/latest/'
data_path = "data/"

def download():
    """ Generate a list of files that are downloaded. Exclude the md5 files from download."""


    try:
        os.makedirs(data_path)
    except:
        pass
    vog = requests.get(url)
    vog = vog.text
    df = pd.DataFrame(pd.read_html(vog)[0]['Name'].dropna())
    file_list = list(df['Name'][1:])

    for f in file_list:
        if not f.lower().endswith("md5"):
            print(f'Downloading {f} to {data_path}')
            urlretrieve(url + f, data_path + f)
    print('Download complete')
    download_check()

def repeat():
    """ Repeat only once the download of files if the checksums are not identical"""

    repeat.has_been_called = True
    download()

def download_check():
    '''Compare md5sum of fileshare files with md5sum of downloaded files
    Run generate_db after verification of data integrity
    Raise: AssertionError,
        restart file download after 10 minutes pause, notify IssueTracker.
        '''

    checksum = requests.get(url)
    checksum = checksum.text
    df = pd.DataFrame(pd.read_html(checksum)[0]['Name'].dropna())
    df_md5 = df[df['Name'].str.contains("md5")]

    downloads = os.listdir(data_path)
    fileshare = list(df_md5['Name'])

    md5_fileshare = []
    md5_download = []
    for file, down in zip(fileshare, downloads):
        #print(file, down)
        (file, _) = urlretrieve(url+file)
        with open(file, "r") as md5_file:
            md5_fileshare.append(md5_file.readline().split()[0])
        md5_download.append(md5(open(data_path+down, "rb").read()).hexdigest())

    try:
        md5_fileshare = sorted(md5_fileshare)
        md5_download = sorted(md5_download)
        assert md5_fileshare == md5_download
    except AssertionError:
        print('Data integrity of downloaded files could not be verified using md5 hash function.')

        if repeat.has_been_called:
            print('Data integrity of 2nd download could not be verified using md5')
            notify()
            print('A notification was sent to CUBE IssueTracker')
        else:
            print('Start new download in 10 minutes ...') # this should only be repeated once
            sleep(600)
            repeat()
    else:
        print('Data integrity verified. Download ok. Proceed with creating MySQL database')
        #__main__  # not sure how to call the functions for db creation!


if __name__ == '__main__':
    repeat.has_been_called = False
    download()