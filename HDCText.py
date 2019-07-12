# Import any needed packages
import requests
import json
import ast
import os
import string
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime
import time

# OPTIONS
# *****************************

# Change the value of HDC_url to the desired Harvard Digital Collections URL
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990058808400203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990003349590203941'
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990043816950203941' # Short 40-page report
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990033211010203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990026755530203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941' # Scientific Papers of Asa Gray
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990025480470203941' # 84 pages
# HDC_url = input("Paste URL from Harvard Digital Collections: ")
manual_pagination = False
manual_page_start = 1
manual_page_end = 11

# FUNCTIONS
# ********************************
# Functions and caching

# Begin caching recipe
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

def search_LibraryCloud(search):
    base_uri = "https://api.lib.harvard.edu/v2/items.dc.json"
    params = {}
    params['q'] = search
    params['limit'] = 20
    params['inDRS'] = True
    params['accessFlag'] = 'P'
    params['contentModel'] = 'PDS DOCUMENT'

    unique_id = params_unique_combination(base_uri,params)

    if unique_id in CACHE_DICTION:
        data_python = CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(base_uri,params = params)
        data_python = json.loads(response_object.text)

        CACHE_DICTION[unique_id] = data_python

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

    records = data_python['items']['dc']

    return records

def extract_nrs_url(lcr): # input: one librarycloud record as dict or many as list
    if type(lcr) == type({}):
        lcr = [lcr]
    urls = []
    for record in lcr:
        for identifier in record['identifier']:
            if 'https://nrs.harvard.edu' in identifier:
                urls.append(identifier)
    return url

def read_HDC_page(url): # input is single url
    params = {}

    unique_id = params_unique_combination(url,params)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(url)
        data = response_object.text

        CACHE_DICTION[unique_id] = data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

        return data

def get_id_from_HDC_URL(page_url,sought_url_stem,tag_name,attribute): # input is for single pds object
    HDC_page = read_HDC_page(page_url)
    # print(HDC_page)
    soup = BeautifulSoup(HDC_page,'html.parser')
    tags = soup.find_all(tag_name) # e.g. 'iframe'
    # print(tags)
    sought_urls = []
    for tag in tags:
        # print(tag)
        if sought_url_stem in tag[attribute]:  # e.g. 'src'
            sought_urls.append(tag[attribute])
    return sought_urls[0]

def get_xml_page_from_fds(drs_id):
    url = 'http://fds.lib.harvard.edu/fds/deliver/' + drs_id
    params = {}

    unique_id = params_unique_combination(url,params)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(url)
        data = response_object.text

        CACHE_DICTION[unique_id] = data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

        return data

def get_text_ids_from_xml(drs_ids): # input can be list of ids or single id
    if type(drs_ids) == type(''):
        drs_ids = [drs_ids]
    book_id_dict = {}
    for id in drs_ids:
        xml_page = get_xml_page_from_fds(id)
        soup = BeautifulSoup(xml_page,'xml')
        tags = soup.find_all('file') # e.g. 'iframe'
        page_ids = []
        for tag in tags:
            if 'text/plain' in tag['MIMETYPE']:  # e.g. 'src'
                page_ids.append(tag.FLocat['xlink:href'])
                # text_file_ids.append(id)
        # print(page_ids)
        book_id_dict[id] = page_ids
    return book_id_dict

def request_txts_from_fds(book_id_dict,page_range): # first input needs to be a dictionary whose values are lists of page ids

    books = {}

    for book_id in list(book_id_dict.keys()):

        pages = []

        page_id_index = 0

        for page in tqdm(page_range):
            successful = False
            while not successful:

                page_id = book_id_dict[book_id][page_id_index]
                url = "http://fds.lib.harvard.edu/fds/deliver/" + page_id
                params = {}

                unique_id = params_unique_combination(url,params)

                if unique_id in CACHE_DICTION:
                    data = CACHE_DICTION[unique_id]
                    successful = True

                else:
                    response_object = requests.get(url)
                    data = response_object.text

                    if 'DOCTYPE' in data:
                        print("\nPage ", str(page_id_index + 1),' (id:', page_id, ') returned html')
                        time.sleep(5)
                    else:
                        successful = True
                        CACHE_DICTION[unique_id] = data

            pages.append(data)

            page_id_index += 1

        books[book_id] = pages

    fileRef = open(CACHE_FNAME,"w")
    data_json = json.dumps(CACHE_DICTION)
    fileRef.write(data_json)
    fileRef.close()

    return books

def trim_iiif_response(resp):
    data = resp.strip()
    data = data.lstrip("?")
    data = data.rstrip(";")
    data = data.strip("()")
    data = ast.literal_eval(data)
    return data

def get_page_count(drs_id):
    api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + drs_id
    api_params_dict = {}
    api_params_dict['callback'] = '?'
    api_params_dict['n'] = '1'

    unique_id = params_unique_combination(api_base_uri,api_params_dict)

    if unique_id in CACHE_DICTION:
        data = CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(api_base_uri,api_params_dict)
        data = response_object.text
        data = trim_iiif_response(data)

        CACHE_DICTION[unique_id] = data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

    page_count = int(data['page']['lastpage'])

    return page_count

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def underscore_puncts_and_whitespace(title):
    filestring = ''
    exclude = string.punctuation + string.whitespace
    for char in title:
        if char in exclude:
            filestring += '_'
        else:
            filestring += char
    if len(filestring) > 50:
        filestring = filestring[0:50]
    return filestring

def create_numeric_name(drs_id):
    t = str(datetime.datetime.now()).split('.')[0]
    filestring = drs_id + " " + t
    filestring = underscore_puncts_and_whitespace(filestring)
    return filestring

def txt_file_plain(book_content,filestring):
    text = ''
    for page in book_content:
        text += page
    filename = 'Results/' + filestring + '.txt'
    file_obj = open(filename,'w',encoding='utf-8')
    file_obj.write(text)
    file_obj.close()

def json_file(book_record,filestring):
    json_data = json.dumps(book_record)
    filename = 'Results/' + filestring + '.json'
    file_obj = open(filename,'w',encoding='utf-8')
    file_obj.write(json_data)
    file_obj.close()

# PART 1. COLLECTING METADATA FOR MULTIPAGE OBJECT
# ********************************
# Takes in an HDC URL and puts out a dictionary with DRS and HDC ids, urls, and a record

# Get associated metadata
print("Getting metadata from LibraryCloud...")
if '?' in HDC_url:
    HDC_url = HDC_url.split('?')[0]
record_permalink = HDC_url
record_id_from_HDC = HDC_url.split('/')[-1]
# print(record_id_from_HDC)

metadata = search_LibraryCloud(record_id_from_HDC)
print(metadata['title'])

# Get DRS ID
print("Finding digital repository service identifier...")
pds_url_stem = 'pds.lib.harvard.edu/pds/view/'
tag_name = 'iframe'
attribute = 'src'
pds_link = get_id_from_HDC_URL(HDC_url,pds_url_stem,tag_name,attribute)
drs_id_from_HDC = pds_link.split('/')[-1]   # e.g. 2585728 , 2678271
print(drs_id_from_HDC)

book_record = {                # TODO: Write a class factory for this dict
    'drs_id' : drs_id_from_HDC,
    'pds_link' : pds_link,
    'record_id' : record_id_from_HDC,
    'permalink' : record_permalink,
    'metadata' : metadata
}

# PART 2. COLLECTING METADATA FOR EACH PAGE
# **************************
# Checks page count using IIIF proxy and then gets an XML document from FDS specifying all the DRS ids for the text files for all the pages of OCR

drs_ids = []
drs_ids.append(drs_id_from_HDC)
if manual_pagination == True:
    page_range = range(manual_page_start,manual_page_end)
else:
    page_count = get_page_count(drs_ids[0])
    page_range = range(1,page_count + 1)
    print("Getting page count...")
    print(page_count)

print("Counting pages avilable...")
book_id_dict = get_text_ids_from_xml(drs_ids)
print(len(book_id_dict[drs_ids[0]]))

# PART 3. GETTING FULL-TEXT OCR FOR ALL PAGES OF OBJECT(S)
# **************************
# Sends a GET request to the FDS for a text file for each page

print("Getting book contents...")
book_contents = request_txts_from_fds(book_id_dict,page_range)

# PART 4. OUTPUTS
# **************************
# Makes a results folder and outputs in various formats

createFolder('./Results/')
filestring = underscore_puncts_and_whitespace(book_record['metadata']['title'])
print("Creating JSON file for metadata...")
try:
    json_file(book_record,filestring)
except:
    filestring = create_numeric_name(book_record['drs_id'])
    json_file(book_record,filestring)
print("Creating text file from OCR...")
txt_file_plain(book_contents[drs_id_from_HDC],filestring)
print("Done! Check results folder.")
