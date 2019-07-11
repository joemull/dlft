# Import any needed packages
import requests
import json
import titlecase
import ast
import os
import string
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime
import time
import string

# OPTIONS
# *****************************

start_with_HDC_url = True # Turn on if you have a URL from Harvard Digital Collections to enter
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990058808400203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990003349590203941'
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990004541160203941'
# HDC_url = 'http://digitalcollections.library.harvard.edu/catalog/fun00001c00689'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990033211010203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990026755530203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941' # Scientific Papers of Asa Gray
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990003349590203941' # Book of Woman's Power
# HDC_url = input("Paste URL from Harvard Digital Collections: ")
manual_pagination = False
manual_page_start = 1 #
manual_page_end = 11 #



start_with_libcloud_search = False # Turn on if you want to start by searching LibraryCloud metadata
# search = input("Search: ")
q = "blue"

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

def extract_nrs_url(lcr): # input: librarycloud record
    for identifier in lcr['identifier']:
        if 'https://nrs.harvard.edu' in identifier:
            return identifier

def read_HDC_page(url):
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

def get_id_from_HDC_URL(page_url,sought_url_stem,tag_name,attribute):
    HDC_page = read_HDC_page(page_url)
    # print(HDC_page)
    soup = BeautifulSoup(HDC_page,'lxml')
    tags = soup.find_all(tag_name) # e.g. 'iframe'
    # print(tags)
    sought_urls = []
    for tag in tags:
        print(tag)
        if sought_url_stem in tag[attribute]:  # e.g. 'src'
            sought_urls.append(tag[attribute])
    return sought_urls[0]

def get_pds_xml_page_from_fds(pds_id):
    url = 'http://fds.lib.harvard.edu/fds/deliver/' + pds_id
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

def get_text_ids_from_xml(pds_ids):
    book_id_dict = {}
    for id in pds_ids:
        xml_page = get_pds_xml_page_from_fds(id)
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

def request_txts_from_fds(book_id_dict,page_range):

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

def get_page_count(pds_id):
    api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + pds_id
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

# PART 1a. SEARCHING METADATA IN LIBRARYCLOUD (OPTIONAL)
# ********************************
# Searches LibraryCloud for individual PDS item records that are parts of multipage objects

if start_with_libcloud_search == True:
    print('Searching LibraryCloud...')
    records = search_LibraryCloud(q)
    nrs_urls = []
    for record in records:
        url = extract_nrs_url(record)   # e,g. https://nrs.harvard.edu/urn-3:FHCL:493855
        # print(url)
        nrs_urls.append(url)

# PART 1b. READING HARVARD DIGITAL COLLECTIONS WEBPAGE
# ********************************
# Takes in an HDC URL and puts out a dictionary with PDS and HDC ids, urls, and a record

if start_with_HDC_url == True:
    # Get associated metadata
    print("Getting metadata from LibraryCloud...")
    record_id_url_stem = 'https://id.lib.harvard.edu/digital_collections/'
    tag_name = 'a'
    attribute = 'href'
    record_permalink = get_id_from_HDC_URL(HDC_url,record_id_url_stem,tag_name,attribute)
    record_id_from_HDC = record_permalink.split('/')[-1]
    # print(record_id_from_HDC)

    metadata = search_LibraryCloud(record_id_from_HDC)
    print(metadata['title'])

    # Get PDS ID
    print("Finding digital repository service identifier...")
    pds_url_stem = 'pds.lib.harvard.edu/pds/view/'
    tag_name = 'iframe'
    attribute = 'src'
    pds_link = get_id_from_HDC_URL(HDC_url,pds_url_stem,tag_name,attribute)
    pds_id_from_HDC = pds_link.split('/')[-1]   # e.g. 2585728 , 2678271
    print(pds_id_from_HDC)

    book_record = {                # TODO: Write a class factory for this dict
        'pds_id' : pds_id_from_HDC,
        'pds_link' : pds_link,
        'record_id' : record_id_from_HDC,
        'permalink' : record_permalink,
        'metadata' : metadata
    }

# PART 2. FINDING MULTIPAGE OBJECT IDs
# **************************
# Sends url for single-page item to name resolution service (NRS) to look up PDS ID of multipage object

if start_with_libcloud_search == True:
    print("Finding digital repository service identifier...")
    pds_ids_from_libcloud = nrs_url_to_pds_id(nrs_urls)
    # print(ids[1])

# PART 3. GETTING FULL-TEXT OCR FOR ALL PAGES OF OBJECT(S)
# **************************
# Sends GET requests to Harvard IIIF, pulls OCR text values from each page, and concatenates

pds_ids = []
if start_with_libcloud_search == True:
    pds_ids.append(pds_ids_from_libcloud)
    print(pds_ids)
else:
    pds_ids.append(pds_id_from_HDC)
    if manual_pagination == True:
        page_range = range(manual_page_start,manual_page_end)
    else:
        page_count = get_page_count(pds_ids[0])   # TODO: Make this use fds rather than iiif
        page_range = range(1,page_count + 1)
        print("Getting page count...")
        print(page_count)

    print("Counting page IDs...")
    book_id_dict = get_text_ids_from_xml(pds_ids)
    print(len(book_id_dict[pds_ids[0]]))
    print("Getting book contents...")
    book_contents = request_txts_from_fds(book_id_dict,page_range)
    # print(books)
    # book_contents = request_from_IIIF(pds_ids,page_range)  # TODO: Add a check in each function with for loops to listify a string input and signal the output to be an instance too, not a list

# for each in list(book_contents.keys()):
#     print(book_contents[each][7])

# PART 4. OUTPUTS
# **************************
# Makes a results folder and outputs in various formats

createFolder('./Results/')
if start_with_HDC_url == True:
    filestring = underscore_puncts_and_whitespace(book_record['metadata']['title'])
    print("Creating JSON file for metadata...")
    try:
        json_file(book_record,filestring)
    except:
        filestring = create_numeric_name(book_record['pds_id'])
        json_file(book_record,filestring)
    print("Creating text file from OCR...")
    txt_file_plain(book_contents[pds_id_from_HDC],filestring)
    print("Done! Check results folder.")
