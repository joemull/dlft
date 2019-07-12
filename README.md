# HDCText
A tool to get the full text of a multipage item in Harvard Digital Collections

## Description
In version 1 of [Harvard Digital Collections](https://library.harvard.edu/digital-collections), users who want the full OCR text of a multi-page item have to copy the OCR text from each page of mirador viewer, which takes multiple clicks and is very time-consuming for more than a few pages.

![alt text][copy-paste-mirador]

This script is a proof of concept for single-click full-text download. The script takes the URL of a Harvard Digital Collections item page as input. After making several calls to HDC, IIIF, LibraryCloud, and FDS (File Delivery Service) to line up the right DRS identifiers, the program gets the text for each page and concatenates them all into a single TXT file. It also puts out a separate JSON file with the associated metadata. Both these files are saved in `/Results/`.

## Dependencies
The program was made with Python 3.7.3 and needs the following modules installed in the run environment:
- `requests`
- `bs4`
- `tqdm`

To install python modules, you can use `pip` with this syntax at a bash console: `pip install <name of module>`

## How to run the program
1. Check to make sure you have the above external modules installed.
2. Change the value of `HDC_url` at the top of `HDCText.py` to the desired URL. Example:

```py
HDC_url = 'https://digitalcollections.library.harvard.edu/catalog/990043816950203941'
```

3. Run `HDCText.py` in a bash console with `python HDCText.py`.
4. Wait. It will take a while, depending on the length of the book. The file delivery service seems to be able to return about 2-5 pages per second.

## Options
You can set the page range manually to get only the OCR for a specified range. Change `False` to `True` and change the numbers in these lines:
```py
manual_pagination = False
manual_page_start = 1
manual_page_end = 11
```

## Future development
This script does a lot of work external to the DRS-HDC system to put together the right OCR data. If this kind of tool is developed natively and put into the Harvard Digital Collections interface as a 'Download Full Text' button, there is no doubt a better way to structure the script that gets the needed DRS identifiers more efficiently.

<!-- Images -->
[copy-paste-mirador]: images/copy-paste-mirador.JPG "User experience of character-recognized text"
