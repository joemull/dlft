# Import any needed packages
import requests
import json
import titlecase
import ast
import os
import string
import funcs
from bs4 import BeautifulSoup
import sys
import string

# PART 0. OPTIONS
# *****************************

start_with_HDC_url = True # Turn on if you have a URL from Harvard Digital Collections to enter
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990058808400203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990003349590203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990004541160203941'
# HDC_url = 'http://digitalcollections.library.harvard.edu/catalog/fun00001c00689'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990033211010203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941'
# HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990026755530203941'
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990014230180203941' # Scientific Papers of Asa Gray
# HDC_url = input("Paste URL from Harvard Digital Collections: ")
manual_pagination = False
manual_page_start = 1 #
manual_page_end = 11 #



start_with_libcloud_search = False # Turn on if you want to start by searching LibraryCloud metadata
# search = input("Search: ")
q = "blue"



# PART 1a. SEARCHING METADATA IN LIBRARYCLOUD (OPTIONAL)
# ********************************
# Searches LibraryCloud for individual PDS item records that are parts of multipage objects

if start_with_libcloud_search == True:
    print('Searching LibraryCloud...')
    records = funcs.search_LibraryCloud(q)
    nrs_urls = []
    for record in records:
        url = funcs.extract_nrs_url(record)   # e,g. https://nrs.harvard.edu/urn-3:FHCL:493855
        # print(url)
        nrs_urls.append(url)

# PART 1b. READING HARVARD DIGITAL COLLECTIONS WEBPAGE
# ********************************
# Takes in an HDC URL and puts out a dictionary with PDS and HDC ids, urls, and a record

if start_with_HDC_url == True:
    # Get PDS ID
    print("Finding digital repository service identifier...")
    pds_url_stem = 'pds.lib.harvard.edu/pds/view/'
    tag_name = 'iframe'
    attribute = 'src'
    pds_link = funcs.get_id_from_HDC_URL(HDC_url,pds_url_stem,tag_name,attribute)
    pds_id_from_HDC = pds_link.split('/')[-1]   # e.g. 2585728 , 2678271
    print(pds_id_from_HDC)

    # Get associated metadata
    print("Getting metadata from LibraryCloud...")
    record_id_url_stem = 'https://id.lib.harvard.edu/digital_collections/'
    tag_name = 'a'
    attribute = 'href'
    record_permalink = funcs.get_id_from_HDC_URL(HDC_url,record_id_url_stem,tag_name,attribute)
    record_id_from_HDC = record_permalink.split('/')[-1]
    # print(record_id_from_HDC)

    metadata = funcs.search_LibraryCloud(record_id_from_HDC)
    print(metadata['title'])

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
    pds_ids_from_libcloud = funcs.nrs_url_to_pds_id(nrs_urls)
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
        page_count = funcs.get_page_count(pds_ids[0])   # TODO: Make this use fds rather than iiif
        page_range = range(1,page_count + 1)
        print("Getting page count...")
        print(page_count)

    print("Counting page IDs...")
    book_id_dict = funcs.get_text_ids_from_xml(pds_ids)
    print(len(book_id_dict[pds_ids[0]]))
    print("Getting book contents...")
    book_contents = funcs.request_txts_from_fds(book_id_dict,page_range)
    # print(books)
    # book_contents = funcs.request_from_IIIF(pds_ids,page_range)  # TODO: Add a check in each function with for loops to listify a string input and signal the output to be an instance too, not a list

# for each in list(book_contents.keys()):
#     print(book_contents[each][7])

# PART 4. OUTPUTS
# **************************
# Makes a results folder and outputs in various formats

funcs.createFolder('./Results/')
if start_with_HDC_url == True:
    filestring = funcs.underscore_puncts_and_whitespace(book_record['metadata']['title'])
    print("Creating JSON file for metadata...")
    try:
        funcs.json_file(book_record,filestring)
    except:
        filestring = funcs.create_numeric_name(book_record['pds_id'])
        funcs.json_file(book_record,filestring)
    print("Creating text file from OCR...")
    funcs.txt_file_plain(book_contents[pds_id_from_HDC],filestring)
    print("Done! Check results folder.")
