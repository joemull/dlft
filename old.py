# Import any needed packages
import requests
import json
import titlecase
import ast
import os
import string
import funcs

# PART 0. OPTIONS
# *****************************

start_with_HDC_url = True # Turn on if you have a URL from Harvard Digital Collections to enter
# HDC_url = input("Paste URL from Harvard Digital Collections: ")0
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990040107870203941'
# HDC_url = 'http://digitalcollections.library.harvard.edu/catalog/990044831370203941'

start_with_libcloud_search = False # Turn on if you want to start by searching LibraryCloud metadata
# search = input("Search: ")
q = "blue"


# PART 1a. SEARCHING METADATA IN LIBRARYCLOUD (OPTIONAL)
# ********************************
# Searches LibraryCloud for individual PDS item records that are parts of multipage objects

if start_with_libcloud_search == True:
    records = funcs.search_LibraryCloud(q)
    eg_record = records[0]
    nrs_url = funcs.extract_nrs_url(eg_record)   # e,g. https://nrs.harvard.edu/urn-3:FHCL:493855
    # print(nrs_url)

# PART 1b. READING HARVARD DIGITAL COLLECTIONS WEBPAGE
# ********************************
# Takes in an HDC URL and puts out the corresponding DRS ID for the multipage object

def read_HDC_page(url):
    base_uri = url
    params = {}

    unique_id = params_unique_combination(base_uri,params)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(base_uri,params = params)
        data = response_object.text

        CACHE_DICTION[unique_id] = data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

    return data

def get_id_from_HDC_URL(url):
    HDC_page = read_HDC_page(url)
    look_for = 'https://pds.lib.harvard.edu/pds/view/'
    pds_viewer_url = HDC_page.find(look_for)
    start_id = pds_viewer_url + len(look_for)
    end_id_plus = start_id + 15
    id = HDC_page[start_id:end_id_plus].split('"')[0]  # TODO Make more durable: what if a page uses a single quote to end the href field for this item?
    return id

if start_with_HDC_url == True:
    drs_id_from_HDC = get_id_from_HDC_URL(HDC_url)


# PART 2. FINDING MULTIPAGE OBJECT ID
# **************************
# Sends url for single-page item to name resolution service (NRS) to look up DRS ID of multipage object

def recognize_name(url):
    base_uri = url
    params = {}

    unique_id = params_unique_combination(base_uri,params)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(base_uri,params = params)
        data = response_object.text

        CACHE_DICTION[unique_id] = data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

    return data

if start_with_libcloud_search == True:
    eg_nrs_url = nrs_url
    mirador = recognize_name(eg_nrs_url)
    # print(type(mirador)) # string
    iiif_id = mirador.find('manifestUri')
    end_iiif_id = mirador.find('MIRADOR_WOBJECTS')
    chunk = mirador[iiif_id:end_iiif_id]
    smidgen = chunk.split('/')[-1]
    snippet = smidgen.split(',')[0]
    num = snippet.split(':')[-1]
    id = num[:-1]
    # print(drs_id)


# PART 3. GETTING FULL-TEXT OCR FOR ALL PAGES OF OBJECT
# **************************
# Sends GET request to Harvard IIIF, pulls OCR text value, and concatenates for each page

def request_from_IIIF(drs_id,page):
    api_base_uri = "https://iiif.lib.harvard.edu/proxy/get/" + drs_id
    api_params_dict = {}
    api_params_dict['callback'] = '?'
    api_params_dict['n'] = page

    unique_id = params_unique_combination(api_base_uri,api_params_dict)

    if unique_id in CACHE_DICTION:
        return CACHE_DICTION[unique_id]
    else:
        response_object = requests.get(api_base_uri,params = api_params_dict)
        data = response_object.text
        question_mark = data.find('?')
        semicolon = data.rfind(';')
        try:
            trimmed_data = data[question_mark+1:semicolon]
            evaluated_data = ast.literal_eval(trimmed_data)
        except:
            print('question mark or semicolon not found on page ' + api_params_dict['n'])

        CACHE_DICTION[unique_id] = evaluated_data

        fileRef = open(CACHE_FNAME,"w")
        data_json = json.dumps(CACHE_DICTION)
        fileRef.write(data_json)
        fileRef.close()

        # Example call URL: https://iiif.lib.harvard.edu/proxy/get/6622876?callback=?&n=3

    return evaluated_data

# Examples NRS IDs:
special = 5387895 # B-8 [Special interview] Case 25s (interviewer R.B.) # https://iiif.lib.harvard.edu/manifests/drs:5387895
rise = 2864318 # Rise and growth of the normal-school idea in the United States # https://iiif.lib.harvard.edu/manifests/drs:2864318
power = 2585728 # The book of woman's power. New York: MacMillan Co., 1911. # https://iiif.lib.harvard.edu/manifests/drs:2585728

drs_id = drs_id_from_HDC
# 51165986 # this one works
# 29425414
# 4310828
# 990128259300203941
# 31849573
# 5143941
# 31849487 # this one works

manual_page_range = [0,] # to print pg. 23, put range as [23,24] ; otherwise leave [0,]

def get_page_count(drs_id):
    response = request_from_IIIF(str(drs_id),page='1')
    page_count = int(response['page']['lastpage'])
    return page_count

page_count = get_page_count(drs_id)
# print(page_count,"...printing page count")

def get_display_label(drs_id):
    response = request_from_IIIF(str(drs_id),page='1')
    displaylabel = response['page']['displaylabel']
    return displaylabel

displaylabel = get_display_label(drs_id)
# print(displaylabel,"...printing display label")

try:
    sum = manual_page_range[0] + manual_page_range[1]
    page_range = manual_page_range
    # print(page_range,"...printing manual page range")
except:
    page_range = [1,page_count]
    # print(page_range,"...printing automatic page range")

# print(range(page_range[0],page_range[1]))

pages = []
for page in range(page_range[0],page_range[1]+1):
    response = request_from_IIIF(str(drs_id),page)
    pages.append(response)

# print(pages,"...printing all page data")

text = ''
for each in pages:
    text += each['page']['text'] + ' [p. ' + each['page']['sequence'] + '] '

# print(text, "...printing concatenated text")

# text = get_multiple_pages(drs_id)

# print('\nIIIF metadata structure')
#
# for thing in list(pages[0]['page'].keys()):
#     print(thing)
#     print(pages[0]['page'][thing])
#     print('\n')

# PART 4. OUTPUTS
# **************************
# Makes a results folder and outputs in various formats

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
createFolder('./Results/')

def underscore_puncts_and_whitespace(str):
    underscored_str = ''
    for char in str:
        if char in string.whitespace:
            underscored_str += '_'
        elif char not in string.punctuation:
            underscored_str += char
        else:
            underscored_str += '_'
    return underscored_str

fn = underscore_punctuation(displaylabel)
f_dir_text = 'Results/' + fn + '.txt'
out_text = open(f_dir_text,'w',encoding='utf-8')
out_text.write(text)
out_text.close()

term = ''
left = len(search.split()) -1
for word in search.split():
    term += word
    if left > 0:
        term += "_"
    left -= 1
fn = 'Results/' + term + '.json'
out_file = open(fn,'w')

if start_with_libcloud_search == True:
    json_out = json.dumps(lib_cloud_response)
    out_file.write(json_out)
    out_file.close()
