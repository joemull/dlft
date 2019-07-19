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

# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990043816950203941' # 40 pages - 6 seconds
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990026755530203941' # 55 pages
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990025480470203941' # 84 pages
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990058808400203941' # 124 pages
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990003349590203941' # 305 pages
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941' # 900 pages - 3 minutes

manual_pagination = False
manual_page_start = 5
manual_page_end = 15

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
    data = data.rstrip(";")
    data = data.strip("()")
    data = ast.literal_eval(data)
    return data

def request_from_iiif_proxy(drs_id,page_range):
    # api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + drs_id
    api_base_uri = "https://pds.lib.harvard.edu/pds/get/" + drs_id
    api_params_dict = {}
    api_params_dict['callback'] = ''

    pages = []

    for page in tqdm(page_range):
        successful = False
        while not successful:
            api_params_dict['n'] = page

            unique_id = params_unique_combination(api_base_uri,api_params_dict)

            if unique_id in CACHE_DICTION:
                data = CACHE_DICTION[unique_id]
                successful = True
            else:
                response_object = requests.get(api_base_uri,api_params_dict)
                data = response_object.text

                if 'page' not in data:
                    print("\nError on page",str(page))
                    print(data)
                else:
                    data = trim_iiif_response(data)
                    CACHE_DICTION[unique_id] = data
                    successful = True

        pages.append(data)

    # print(pages)
    save_cache(CACHE_DICTION)
    return pages

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

        save_cache(CACHE_DICTION)

        return data

def get_text_ids_from_xml(drs_id,page_range): # input must be single id
    xml_page = get_xml_page_from_fds(drs_id)
    soup = BeautifulSoup(xml_page,'xml')
    tags = soup.find_all('file') # e.g. 'iframe'
    page_id_list = []
    for tag in tags:
        if 'text/plain' in tag['MIMETYPE']:  # e.g. 'src'
            page_id_list.append(tag.FLocat['xlink:href'])
            # text_file_ids.append(id)
    # print(page_ids)
    page_id_dict = {}
    for page in page_range:
        page_id_dict[page] = page_id_list[page-1]
    return page_id_dict

def request_txts_from_fds(page_ids): # input must be dictionary whose keys are page numbers and values are DRS ids for FDS txt files

    pages = {}

    for page_number in tqdm(sorted(list(page_ids.keys()))):
        successful = False
        while not successful:

            url = "http://fds.lib.harvard.edu/fds/deliver/" + page_ids[page_number]
            params = {}

            unique_id = params_unique_combination(url,params)

            if unique_id in CACHE_DICTION:
                data = CACHE_DICTION[unique_id]
                successful = True

            else:
                response_object = requests.get(url)
                data = response_object.text

                if 'DOCTYPE' in data:
                    one = 1
                    # print("\nPage {} (id: {} ) returned error".format(str(page_number),page_ids[page_number]))
                else:
                    successful = True
                    CACHE_DICTION[unique_id] = data

        pages[page_number] = data

    save_cache(CACHE_DICTION)

    return pages

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def name_to_filestring(title,page_range):
    filestring = ''
    exclude = string.punctuation + string.whitespace
    for char in title:
        if char in exclude:
            filestring += '_'
        else:
            filestring += char
    if len(filestring) > 50:
        filestring = filestring[0:50]
    filestring = "{}_pp_{}-{}".format(filestring,min(page_range),max(page_range))
    return filestring

def create_numeric_name(drs_id,page_range):
    t = str(datetime.datetime.now()).split('.')[0]
    filestring = drs_id + " " + t
    filestring = name_to_filestring(filestring,page_range)
    return filestring

def txt_file_plain(pages,filestring):
    text = ''
    for page in sorted(list(pages.keys())):
        ocr = pages[page]
        text += ocr
    filename = 'Results/' + filestring + '.txt'
    file_obj = open(filename,'w',encoding='utf-8')
    file_obj.write(text)
    file_obj.close()

# GET DRS ID
# *****************

print("Finding digital repository service identifier...")
unique_string = 'copyManifestToClipBoard'
tag_name = 'a'
attribute = 'onclick'
manifest_string = get_id_from_HDC_URL(HDC_url,unique_string,tag_name,attribute)
iiif_manifest_link = manifest_string[len(unique_string):].strip("('')")
drs_id_from_HDC = iiif_manifest_link.split(':')[-1]   # e.g. 2585728 , 2678271
print(drs_id_from_HDC)

# SET PAGE RANGE
# ***************

if manual_pagination == True:
    page_range = range(manual_page_start,manual_page_end + 1)
    print('Pages {}-{} requested...'.format(manual_page_start,manual_page_end))
else:
    page_count = int(request_from_iiif_proxy(drs_id_from_HDC,range(1,2))[0]['page']['lastpage'])
    page_range = range(1,page_count + 1)
    print("Getting page count...")
    print(page_count)

# GET PAGE CONTENTS
# ***************

print("Getting page contents...")
page_ids = get_text_ids_from_xml(drs_id_from_HDC,page_range)
# print(page_ids)
pages = request_txts_from_fds(page_ids)

# OUTPUT FILE
# ***************

createFolder('./Results/')
displaylabel = request_from_iiif_proxy(drs_id_from_HDC,range(1,2))[0]['page']['displaylabel']
filestring = name_to_filestring(displaylabel,page_range)
print("Creating text file from OCR...")
try:
    txt_file_plain(pages,filestring)
except:
    filestring = create_numeric_name(drs_id_from_HDC,page_range)
    txt_file_plain(pages,filestring)
print("Done! Check Results folder.")
