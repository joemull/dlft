import requests
import json
import titlecase
import ast
import os
import string
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime

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
    soup = BeautifulSoup(HDC_page,'html.parser')
    tags = soup.find_all(tag_name) # e.g. 'iframe'
    sought_urls = []
    for tag in tags:
        if sought_url_stem in tag[attribute]:  # e.g. 'src'
            sought_urls.append(tag[attribute])
    return sought_urls[0]

def nrs_url_to_pds_id(urls):
    ids = []
    params = {}
    for url in urls:
        unique_id = params_unique_combination(url,params)

        if unique_id in CACHE_DICTION:
            data = CACHE_DICTION[unique_id]
        else:
            response_object = requests.get(url)
            data = response_object.text

            CACHE_DICTION[unique_id] = data

        iiif_id = data.find('manifestUri')
        end_iiif_id = data.find('MIRADOR_WOBJECTS')
        chunk = data[iiif_id:end_iiif_id]
        smidgen = chunk.split('/')[-1]
        snippet = smidgen.split(',')[0]
        num = snippet.split(':')[-1]
        id = num[:-1]

        ids.append(id)

    fileRef = open(CACHE_FNAME,"w")
    data_json = json.dumps(CACHE_DICTION)
    fileRef.write(data_json)
    fileRef.close()

    return ids

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

            page_id = book_id_dict[book_id][page_id_index]
            url = "http://fds.lib.harvard.edu/fds/deliver/" + page_id
            params = {}

            unique_id = params_unique_combination(url,params)

            if unique_id in CACHE_DICTION:
                data = CACHE_DICTION[unique_id]

            else:
                response_object = requests.get(url)
                data = response_object.text

                CACHE_DICTION[unique_id] = data

            if 'DOCTYPE' in data:
                print("\nPage ", str(page_id_index + 1),' (id:', page_id, ') returned html')

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

def request_from_IIIF(pds_ids,page_range = 'auto'):

    books = {}

    for id in pds_ids:
        api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + id
        api_params_dict = {}
        api_params_dict['callback'] = '?'

        pages = []

        for page in page_range:

            api_params_dict['n'] = page

            unique_id = params_unique_combination(api_base_uri,api_params_dict)
            print(unique_id)
            if unique_id in CACHE_DICTION:
                data = CACHE_DICTION[unique_id]

            else:
                # Example call URL: https://iiif.lib.harvard.edu/proxy/get/6622876?callback=?&n=3
                response_object = requests.get(api_base_uri,params = api_params_dict)
                data = response_object.text
                data = trim_iiif_response(data)

                CACHE_DICTION[unique_id] = data

            page = data['page']['text']
            pages.append(page)

        books[id] = pages

    fileRef = open(CACHE_FNAME,"w")
    data_json = json.dumps(CACHE_DICTION)
    fileRef.write(data_json)
    fileRef.close()

    return books

def get_display_label(pds_id):
    response = request_from_IIIF(str(pds_id),page='1')
    displaylabel = response['page']['displaylabel']
    return displaylabel

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
