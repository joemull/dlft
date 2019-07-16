# DownLoad Full Text
A tool to get the full text of a multipage item in Harvard Digital Collections

## Description
In version 1 of [Harvard Digital Collections](https://library.harvard.edu/digital-collections), users who want the full OCR text of a multi-page item have to copy it from a popup in the mirador viewer, which takes multiple clicks and is time-consuming for more than a few pages.

![alt text][copy-paste-mirador]

[dlft](https://github.com/joemull/dlft) is a proof of concept for single-click full-text download. The script takes the URL of a Harvard Digital Collections item page as input. After locating the Digital Repository Service (DRS) identifier on the HDC page, the script calls the endpoint `https://pds.lib.harvard.edu/pds/get/` to get the text for each page and concatenates them all into a single TXT file, saved in `/Results/`.

## Dependencies
The program was made with Python 3.7.3 and needs the following modules installed in the run environment:
- `requests`
- `bs4`
- `tqdm`

To install python modules, you can use `pip` with this syntax at a bash console: `pip install <name of module>`

## How to run the program
1. Check to make sure you have the above external modules installed.
2. Change the value of `HDC_url` at the top of `dlft.py` to the desired URL. Example:

```py
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990043816950203941'
```

3. Run `dlft.py` in a bash console with `python dlft.py`.
4. Wait. It will take a while, depending on the length of the book. The page delivery service seems to be able to return about 2-3 pages per second.

## Options
You can set the page range manually to get only the OCR for a specified range. Change `False` to `True` and change the numbers in these lines:
```py
manual_pagination = False
manual_page_start = 1
manual_page_end = 11
```

## Future development
Before this tool is added to the interface of Harvard Digital Collections, it will need to be rewritten using javascript. More work might also be done to find the best endpoint. `https://pds.lib.harvard.edu/pds/get/` may not be as fast as `http://fds.lib.harvard.edu/fds/deliver/`, but the File Delivery Service requires the exact DRS ID for each txt file, which needs to be scraped from a comprehensive XML page available from the same endpoint. 

<!-- Images -->
[copy-paste-mirador]: images/copy-paste-mirador.JPG "The user experience of downloading character-recognized text for each page"
