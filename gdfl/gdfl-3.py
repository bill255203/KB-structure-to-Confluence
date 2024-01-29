
from __future__ import print_function
import httplib2
import os
import sys
import codecs
import webbrowser
from bs4 import BeautifulSoup

from operator import itemgetter, attrgetter
from apiclient import errors, discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import requests
from requests.auth import HTTPBasicAuth
import json
API_TOKEN = "ATATT3xFfGF0sLJ4nSgF8FFlk-0XUlaYTBUjIx2MwqFLQDVzQ46YiPN2lcCalzGrQ4Vu4acu75gquQSEyBay2pXdOJ5z4mj4uNWnP21zeXaRe4ZXWiTtUe3bro8jVSZTwv5G0jGdDavQOlghePlabFysENgS7ZseNsBp-Gu6011sHphM-w3cZaA=B4157CF9"
SPACE_ID = "2043871841"
PARENT_ID = "2044466099"
EMAIL = "bill.liao@mile.cloud"

def create_confluence_page(title, parent_id, body_value):
    url = "https://cloudmile4service.atlassian.net/wiki/api/v2/pages"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "spaceId": SPACE_ID,
        "status": "current",
        "title": title,
        "parentId": parent_id,
        "body": {
            "representation": "storage",
            "value": body_value
        }
    })

    response = requests.request("POST", url, data=payload, headers=headers, auth=auth)
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    response_data = json.loads(response.text)  # Parse the JSON response
    page_id = response_data.get('id')  # Get the 'id' field from the response
    print(page_id)
    return page_id


try:
    import argparse

    parent = argparse.ArgumentParser(parents=[tools.argparser])
    parent.add_argument("-f", "--folder_id", help="Enter folder ID to list")
    parent.add_argument("-c", "--files", action='store_false',
                        help="To include child files in folders")
    flags = parent.parse_args()
except ImportError:
    flags = None

# This script is dervived from Googles own Google Drive API Python
# Quickstart and pulls together many of the reference samples.

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/dgdfl-secrets.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Drive Folder List'
created_pages = {}

def get_mime_type_keyword(item):
    # Check if 'mimeType' is in the item dictionary
    if 'mimeType' in item:
        mime_type = item['mimeType']
        # Split the mimeType by '.' and get the last part
        parts = mime_type.split('.')
        # Check if it's a Google mimeType
        if parts[0] == 'application/vnd' and len(parts) > 2:
            # Extract the key word (like 'audio', 'document', etc.)
            key_word = parts[-1]
            # Return the extracted word
            return "(" + key_word + ")"
        else:
            return ""
    else:
        return ""

def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    client_secret = os.path.join(os.curdir, CLIENT_SECRET_FILE)
    if not client_secret:
        print('Follow the instructions in Step 1 on the following '
              'page:\nhttps://developers.google.com/drive/v3/web/quickstart/python')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gdfl-secrets.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_folders(service, folder_id, level, Html_file, folders_only, drivetype, parent_id):
    """Get's the folders in the parent folder
    """
    global FOLDERCOUNT
    global FILECOUNT
    global DEEPEST
    FOLDERCOUNT = 0
    FILECOUNT = 0
    DEEPEST = 0
    page_token = None
    while True:
        try:
            param = {}
            if page_token:
                param['pageToken'] = page_token

            if folders_only == True:
                query = "'" + folder_id + "' in parents and mimeType='application/vnd.google-apps.folder'"
            else:
                query = "'" + folder_id + "' in parents"

            if drivetype == 'Shared Drive':
                results = service.files().list(
                    q=query,
                    driveId=folder_id,
                    corpora='drive',
                    includeItemsFromAllDrives='true',
                    supportsAllDrives='true',
                    fields="nextPageToken, files(id, name, parents, webViewLink, iconLink, mimeType)").execute()
            else:
                results = service.files().list(
                    q=query, orderBy='folder',
                    fields="nextPageToken, files(id, name, parents, webViewLink, iconLink)",
                    **param).execute()
            
            items = results.get('files', [])
            items.sort(key=itemgetter('name'))
            level += 1
            if items:
                html_list1 = """"""
                for item in items:
                    print(html_list1)
                    if drivetype == 'Shared Drive':
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            FOLDERCOUNT += 1
                            if level > DEEPEST:
                                DEEPEST = level
                        else:
                            FILECOUNT += 1
                    current_id = item['id']
                    itemname = item['name']
                    indent = ' ' * level
                    depth = str(level)
                    mime_type = get_mime_type_keyword(item)
                    html_list2 = """<span>            
                    <a href='""" + item['webViewLink'] \
                                + """'> """ + mime_type + itemname + """</a>"""
                    if item['mimeType'] != 'application/vnd.google-apps.folder':
                        html_list1 += html_list2
                        continue
                    Html_file.write(html_list2)
                
                    title = str(itemname)
                    if title in created_pages:
                        # Increment the count for this title
                        created_pages[title] += 1
                        # Append the count to make the title unique
                        title = f"KB_{itemname}"
                    else:
                        # Add the new title with a count of 0
                        created_pages[title] = 0

                    soup = BeautifulSoup(html_list2, 'html.parser')
                    body_value = str(soup)
                    parent_page_id = create_confluence_page(title, parent_id, body_value)
                    get_child_sub_folders(service, current_id, level, Html_file, folders_only, folder_id, drivetype, parent_page_id, itemname, title)
                    Html_file.write("</span>\n")
                title = str(itemname)
                if title in created_pages:
                    # Increment the count for this title
                    created_pages[title] += 1
                    # Append the count to make the title unique
                    title = f"KB_files"
                else:
                    # Add the new title with a count of 0
                    created_pages[title] = 0
                    
                soup = BeautifulSoup(html_list1, 'html.parser')
                body_value = str(soup)
                create_confluence_page(title, parent_id, body_value)
                page_token = results.get('nextPageToken')

            if not page_token:
                break

        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break

def get_child_sub_folders(service, parent_id, level, Html_file, folders_only, folder_id, drivetype, parent_page_id, itemname, parent_title):
    """Get's the folders in the child folder
    """
    global FOLDERCOUNT
    global FILECOUNT
    global DEEPEST
    
    page_token = None
    while True:
        try:
            param = {}
            if page_token:
                param['pageToken'] = page_token

            if folders_only == True:
                query = "'" + parent_id + "' in parents and mimeType='application/vnd.google-apps.folder'"
            else:
                query = "'" + parent_id + "' in parents"

            if drivetype == 'Shared Drive':
                results = service.files().list(
                    q=query,
                    driveId=folder_id,
                    corpora='drive',
                    includeItemsFromAllDrives='true',
                    supportsAllDrives='true',
                    fields="nextPageToken, files(id, name, parents, webViewLink, iconLink, mimeType)").execute()
            else:
                results = service.files().list(
                    q=query, orderBy='folder',
                    fields="nextPageToken, files(id, name, parents, webViewLink, iconLink)",
                    **param).execute()

            items = results.get('files', [])
            items.sort(key=itemgetter('name'))
            prev_level = level
            level += 1
            files_title = parent_title
            has_file = 0
            if items:
                html_list1 = """
                <ul>"""
                for item in items:
                    if drivetype == 'Shared Drive':
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            FOLDERCOUNT += 1
                            if level > DEEPEST:
                                DEEPEST = level
                        else:
                            FILECOUNT += 1
                    child_id = item['id']
                    childname = item['name']
                    indent = '  ' * level
                    depth = str(level)
                    mime_type = get_mime_type_keyword(item)
                    if level > prev_level:
                        html_list3 = """
                    <li><a href='""" + item['webViewLink'] \
                                    + """'> """ + mime_type + childname + """</a>"""
                        Html_file.write(html_list3)
                    else:
                        html_list3 = """
                        <li><a href='""" + item['webViewLink'] \
                                    + """'> """+ mime_type + childname  + """</a>"""
                        Html_file.write(html_list3)
                    if item['mimeType'] != 'application/vnd.google-apps.folder':
                        html_list1 += html_list3
                        has_file = 1
                        continue

                    prev_level = level
                    title = str(childname)
                    if title in created_pages:
                        # Increment the count for this title
                        created_pages[title] += 1
                        # Append the count to make the title unique
                        title = f"{parent_title}_{childname}"
                    else:
                        # Add the new title with a count of 0
                        created_pages[title] = 0

                    soup = BeautifulSoup(html_list3, 'html.parser')
                    body_value = str(soup)
                    parent_title = title
                    new_parent_page_id = create_confluence_page(title, parent_page_id, body_value)
                    get_child_sub_folders(service, child_id, level, Html_file, folders_only, folder_id, drivetype, new_parent_page_id, childname, parent_title)
                page_token = results.get('nextPageToken')
                Html_file.write(""" </ul>""")
                if has_file:
                    title = str(files_title) + "_files"
                    if title in created_pages:
                        # Increment the count for this title
                        created_pages[title] += 1
                        # Append the count to make the title unique
                        title = f"{parent_title}_{files_title}_files"
                    else:
                        # Add the new title with a count of 0
                        created_pages[title] = 0

                    soup = BeautifulSoup(html_list1, 'html.parser')
                    body_value = str(soup)
                    create_confluence_page(title, parent_page_id, body_value)

            if not page_token:
                break

        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break

def main():
    """Uses Google Drive API to get the parent folder
    Gets the parent folder specified in args or uses the users Root folder
    Calls the function to get sub folders and loops through all child folders.
    Produces the html file output and opens it in the default browser.
    """
    foldername = ''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    
    if not flags.folder_id:
        folder_id = 'root'
        drivetype = 'My Drive'
    else:
        folder_id = flags.folder_id

        try:
            folder = service.files().get(fileId=folder_id).execute()
            foldername = folder['name']
            drivetype = 'My Drive'
            print("Folder ID " + folder_id + " is a Google Drive Folder called: " + foldername)
        except errors.HttpError as error:
            try:
                folder = service.drives().get(
                  driveId=folder_id).execute()
                foldername = folder['name']
                drivetype = 'Shared Drive'
                print("Folder ID " + folder_id + " is a Shared Drive named: " + foldername)
            except errors.HttpError as error:
                foldername = ''

    if not foldername:
       print('An error occurred %s' % error)
       exit()

    
    if (sys.version_info < (3, 0)):
        if isinstance(foldername, str):
            foldername = unicode(foldername, "utf-8")

    folders_only = flags.files
    level = 0

    html_file = foldername + '.html'
    Html_file = open(html_file, "w")
    html_start = """"""
    Html_file.write(html_start)
    header = 'Folder structure for: ' + folder['name']
    html_heading = """<h1>""" + header + """</h1>"""
    if (sys.version_info < (3, 0)):
        Html_file.write(html_heading.encode("utf-8"))
    else:
        Html_file.write(html_heading)
    html_list1 = """
    <UL>
      <li>
      <span>""" + folder['name'] + """</span>"""
    if (sys.version_info < (3, 0)):
        print('Building folder structure for {0}'.format(folder['name'].encode("utf-8")))
    else:
        print('Building folder structure for {0}'.format(folder['name']))
    parent_id = create_confluence_page("KB's CATALOG", PARENT_ID, """<a href="https://drive.google.com/drive/u/0/folders/0ANbyjco9413kUk9PVA"> KB here</a>""")
    get_folders(service, folder_id, level, Html_file, folders_only, drivetype, parent_id)
    
    footer = ""
    if drivetype == 'Shared Drive':
        global FOLDERCOUNT
        global FILECOUNT
        global DEEPEST
        FOLDERCOUNT = 0
        FILECOUNT = 0
        DEEPEST = 0
        TOTALCOUNT = FOLDERCOUNT + FILECOUNT

    html_end = """
          </li>
        </ul>
 """
    Html_file.write(html_end)
    Html_file.close()
    if (sys.version_info < (3, 0)):
        webbrowser.open(html_file.encode("utf-8"))
    else:
        webbrowser.open(html_file)

if __name__ == '__main__':
    main()
