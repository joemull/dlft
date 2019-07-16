import requests
import json
import ast
import os
import string
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime
import time

# INPUT
# **********************

HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990025480470203941' # 84 pages
manual_pagination = False
manual_page_start = 1
manual_page_end = 11

# FUNCTIONS
# ************************

CACHE_FNAME = "cache.json"
try:
    f = open(CACHE_FNAME,'r')
    content_str = f.read()
    CACHE_DICTION = json.loads(content_str)
    f.close()
except:
    CACHE_DICTION = {}

def params_unique_combination(baseurl,params_d,private_keys=["apikey"]):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        if k not in private_keys:
            res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)

def save_cache(CACHE_DICTION):
    fileRef = open(CACHE_FNAME,"w")
    data_json = json.dumps(CACHE_DICTION)
    fileRef.write(data_json)
    fileRef.close()

    def read_HDC_page(url): # input is single url
        params = {}

        unique_id = params_unique_combination(url,params)

        if unique_id in CACHE_DICTION:
            return CACHE_DICTION[unique_id]
        else:
            response_object = requests.get(url)
            data = response_object.text

            CACHE_DICTION[unique_id] = data

            save_cache(CACHE_DICTION)

            return data

def read_HDC_page(url): # input is single url
    params = {}

    unique_id = params_unique_combination(url,params)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(url)
        data = response_object.text

        CACHE_DICTION[unique_id] = data

        save_cache(CACHE_DICTION)

        return data

def get_id_from_HDC_URL(page_url,sought_string,tag_name,attribute): # input is for single pds object
    HDC_page = read_HDC_page(page_url)
    # print(HDC_page)
    soup = BeautifulSoup(HDC_page,'html.parser')
    tags = soup.find_all(tag_name) # e.g. 'iframe'
    # print(tags)
    sought_urls = []
    for tag in tags:
        # print(tag)
        if attribute in tag.attrs:
            if sought_string in tag[attribute]:  # e.g. 'src'
                sought_urls.append(tag[attribute])
    return sought_urls[0]

def trim_iiif_response(resp):
    data = resp.strip()
    data = data.lstrip("?")
    data = data.rstrip(";")
    data = data.strip("()")
    data = ast.literal_eval(data)
    return data

def request_from_iiif_proxy(drs_id,page_range):
    api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + drs_id
    api_params_dict = {}
    api_params_dict['callback'] = '?'
    pages = []
    for page in page_range:
        api_params_dict['n'] = page

        unique_id = params_unique_combination(api_base_uri,api_params_dict)

        if unique_id in CACHE_DICTION:
            data = CACHE_DICTION[unique_id]
        else:
            response_object = requests.get(api_base_uri,api_params_dict)
            data = response_object.text
            print(data)
            data = trim_iiif_response(data)

            # CACHE_DICTION[unique_id] = data
        pages.append(data)
    # save_cache(CACHE_DICTION)

    return data

# GET DRS ID
# *****************

print("Finding digital repository service identifier...")
unique_string = 'copyManifestToClipBoard'
tag_name = 'a'
attribute = 'onclick'
manifest_string = get_id_from_HDC_URL(HDC_url,unique_string,tag_name,attribute)
iiif_manifest_link = manifest_string[len(unique_string):].strip("('')")
drs_id_from_HDC = iiif_manifest_link.split(':')[-1]   # e.g. 2585728 , 2678271
# print(drs_id_from_HDC)

# GET PAGE COUNT
if manual_pagination == True:
    page_range = range(manual_page_start,manual_page_end)
else:
    page_count = int(request_from_iiif_proxy(drs_id_from_HDC,range(1,1))['page']['lastpage'])
    page_range = range(1,page_count + 1)
    print("Getting page count...")
    print(page_count)

# GET PAGE CONTENTS
# ***************
