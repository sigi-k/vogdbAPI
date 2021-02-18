from urllib.request import urlretrieve
import requests
import pandas as pd
import os
from hashlib import md5

url = 'http://fileshare.csb.univie.ac.at/vog/latest/'
data_path = "data/"

def check():
    """Compare md5sum of fileshare files with md5sum of downloaded files"""

    try:
        os.makedirs(data_path)
    except:
        pass

    # load the filenames from fileshare into a dataframe
    checksum = requests.get(url)
    checksum = checksum.text
    df = pd.DataFrame(pd.read_html(checksum)[0]['Name'].dropna())

    # sort a list of all md5 files from fileshare
    df_md5 = df[df['Name'].str.contains("md5")]
    fileshare = list(df_md5['Name'])
    fileshare = sorted(fileshare)

    # sort a list of all data filenames from fileshare, this serves a reference to the list of downloaded files
    df_files = df[df['Name'].str.contains("md5") == False]
    files = list(df_files['Name'][1:])
    files = sorted(files)

    # sort a list of downloaded files in data directory
    downloads = os.listdir(data_path)
    downloads = sorted(downloads)

    # check if all files from fileshare are in data directory and download if not existent
    for f, down in zip(files, downloads):
        if f not in downloads:
            print(f'downloading {f} from {url}')
            urlretrieve(url + f, data_path + f)

    # extract hash code from md5 files retrieved from fileshare
    for web, down in zip(fileshare, downloads):
        (web, _) = urlretrieve(url + web)
        with open(web, "r") as md5_file:
            md5_check = md5_file.readline().split()[0]
        # get hash code from downloaded files and compare with hash code from fileshare
        md5_download = md5(open(data_path + down, "rb").read()).hexdigest()
        if md5_download != md5_check:
            # download files from fileshare if the hash codes are not the same
            print(f'Updating {down} from fileshare')
            urlretrieve(url + down, data_path + down)
        else:
            print(f'{down} seems up-to-date and complete.')

if __name__ == '__main__':
    check()