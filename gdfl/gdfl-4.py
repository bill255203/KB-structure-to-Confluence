
from __future__ import print_function
import httplib2
import os
import sys
import codecs
import json
from bs4 import BeautifulSoup
import copy
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

def load_or_create_json_file(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # If the file does not exist, create it with empty dictionary content
        with open(file_name, 'w') as file:
            json.dump({}, file)
            return {}

created_pages = load_or_create_json_file('created_pages.json')
prefix_titles = load_or_create_json_file('prefix_titles.json')
remaining_pages = created_pages.copy()
def create_confluence_page(title, parent_id, body_value, prefixed_title):
    print("create")
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
    version_number = response_data.get('version', {}).get('number')
    print(page_id)
    created_pages[title] = [page_id, version_number, prefixed_title]
    prefix_titles[prefixed_title] = True
    return page_id
    
def update_confluence_page(title, body_value, update_id, version_number, prefixed_title):
    print("update")
    print(version_number)
    url = f"https://cloudmile4service.atlassian.net/wiki/api/v2/pages/{update_id}"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps( {
        "id": update_id,
        "status": "current",
        "title": title,
        "body": {
            "representation": "storage",
            "value": body_value
        },
        "version": {
            "number": version_number,
            "message": str(version_number)
        }
    } )
    print(payload)
    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    response_data = json.loads(response.text)  # Parse the JSON response
    page_id = response_data.get('id')  # Get the 'id' field from the response
    version_number = response_data.get('version', {}).get('number')
    print(page_id)
    created_pages[title] = [page_id, version_number, prefixed_title]
    del remaining_pages[str(title)]
    print(f"Remaining Pages After Deletion: {remaining_pages}")
    return page_id

def delete_page(delete_title, delete_id, delete_prefixed_title):
    print(delete_id)
    url = f"https://cloudmile4service.atlassian.net/wiki/api/v2/pages/{delete_id}"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    response = requests.request(
        "DELETE",
        url,
        auth=auth
    )
    del created_pages[delete_title]
    del prefix_titles[delete_prefixed_title]
    print(response.text, response.status_code)

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
                    includeItemsFromAllDrives='false',
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
                    soup = BeautifulSoup(html_list2, 'html.parser')
                    body_value = str(soup)
                    original_title = title
                    prefixed_title = f"KB_{title}"

                    # Case 1: Create Original Page (if neither original nor prefixed title is in any hashmap)
                    if original_title not in created_pages:
                        parent_page_id = create_confluence_page(original_title, parent_id, body_value, prefixed_title)
                    # Case 2: Create Prefixed Page (if original is in created_pages but prefixed is not in any hashmap)
                    elif prefixed_title not in prefix_titles:
                        parent_page_id = create_confluence_page(prefixed_title, parent_id, body_value, prefixed_title)
                    # Case 3: Update Prefixed Page (if prefixed is in prefix_titles)
                    elif prefixed_title in created_pages:
                        update_id, version_number = int(created_pages[prefixed_title][0]), created_pages[prefixed_title][1]
                        parent_page_id = update_confluence_page(prefixed_title, body_value, update_id, version_number + 1, prefixed_title)
                    # Case 4: Update Original Page (if original is in created_pages but not in prefix_titles)
                    else:
                        update_id, version_number = int(created_pages[original_title][0]), created_pages[original_title][1]
                        parent_page_id = update_confluence_page(original_title, body_value, update_id, version_number + 1, prefixed_title)

                    get_child_sub_folders(service, current_id, level, Html_file, folders_only, folder_id, drivetype, parent_page_id, itemname, title)
                    Html_file.write("</span>\n")
                title = str(itemname)
                if title in created_pages:
                    title = f"KB_files"
                soup = BeautifulSoup(html_list1, 'html.parser')
                body_value = str(soup)
                if title in created_pages:
                    update_id, version_number = int(created_pages[title][0]), created_pages[title][1]
                    update_confluence_page(title, body_value, update_id, version_number + 1, prefixed_title)
                else:
                    create_confluence_page(title, parent_id, body_value, title)
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
                    includeItemsFromAllDrives='false',
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
            current_title = parent_title
            has_file = 0
            if items:
                html_list1 = """
                <ul>"""
                for item in items:
                    print(parent_title)
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
                    soup = BeautifulSoup(html_list3, 'html.parser')
                    body_value = str(soup)
                    
                    title = str(childname)
                    original_title = title
                    prefixed_title = f"{parent_title}_{title}"
                
                    # Case 1: Create Original Page (if neither original nor prefixed title is in any hashmap)
                    if original_title not in created_pages:
                        new_parent_page_id = create_confluence_page(original_title, parent_page_id, body_value, prefixed_title)
                    # Case 2: Create Prefixed Page (if original is in created_pages but prefixed is not in any hashmap)
                    elif prefixed_title not in prefix_titles:
                        new_parent_page_id = create_confluence_page(prefixed_title, parent_page_id, body_value, prefixed_title)
                    # Case 3: Update Prefixed Page (if prefixed is in prefix_titles)
                    elif prefixed_title in created_pages:
                        update_id, version_number = int(created_pages[prefixed_title][0]), created_pages[prefixed_title][1]
                        new_parent_page_id = update_confluence_page(prefixed_title, body_value, update_id, version_number + 1, prefixed_title)
                    # Case 4: Update Original Page (if original is in created_pages but not in prefix_titles)
                    else:
                        update_id, version_number = int(created_pages[original_title][0]), created_pages[original_title][1]
                        new_parent_page_id = update_confluence_page(original_title, body_value, update_id, version_number + 1, prefixed_title)
                    print(parent_title)
                    get_child_sub_folders(service, child_id, level, Html_file, folders_only, folder_id, drivetype, new_parent_page_id, childname, title)
                page_token = results.get('nextPageToken')
                Html_file.write(""" </ul>""")
                if has_file:
                    soup = BeautifulSoup(html_list1, 'html.parser')
                    body_value = str(soup)
                    title = str(current_title) + "_files"
                    original_title = title
                    prefixed_title = f"{parent_title}_{current_title}_files"

                    # Case 1: Create Original Page (if neither original nor prefixed title is in any hashmap)
                    if original_title not in created_pages:
                        create_confluence_page(original_title, parent_page_id, body_value, prefixed_title)
                    # Case 2: Create Prefixed Page (if original is in created_pages but prefixed is not in any hashmap)
                    elif prefixed_title not in prefix_titles:
                        create_confluence_page(prefixed_title, parent_page_id, body_value, prefixed_title)
                    # Case 3: Update Prefixed Page (if prefixed is in prefix_titles)
                    elif prefixed_title in created_pages:
                        update_id, version_number = int(created_pages[prefixed_title][0]), created_pages[prefixed_title][1]
                        update_confluence_page(prefixed_title, body_value, update_id, version_number + 1, prefixed_title)
                    # Case 4: Update Original Page (if original is in created_pages but not in prefix_titles)
                    else:
                        update_id, version_number = int(created_pages[original_title][0]), created_pages[original_title][1]
                        update_confluence_page(original_title, body_value, update_id, version_number + 1, prefixed_title)
            if not page_token:
                break

        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            break

def main():
    foldername = ''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    print(f"Remaining Pages: {remaining_pages}")
    
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
       print('Please add a flag with folder name in the command line %s' % error)
       exit()
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
    root_title = "bill1"
    root_value = """<a href="https://drive.google.com/drive/u/0/folders/0ANbyjco9413kUk9PVA"> KB here</a>"""
    if root_title in created_pages:
        update_id, version_number = int(created_pages[root_title][0]), created_pages[root_title][1]
        parent_id = update_confluence_page(root_title, root_value, update_id, version_number + 1, root_title)
    else:
        parent_id = create_confluence_page(root_title, PARENT_ID, root_value, root_title)
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
    
    print(f"Final Remaining Pages: {remaining_pages}")
    for delete_title, info in remaining_pages.items():
        delete_id, version_number, delete_prefixed_title = int(info[0]), info[1], info[2]
        delete_page(delete_title, delete_id, delete_prefixed_title)
    
    print(f"Final Created Pages: {created_pages}")
    filename = 'created_pages.json'
    with open(filename, 'w') as json_file:
        json.dump(created_pages, json_file, indent=4)
        
    print(f"Final prefix titles: {prefix_titles}")
    filename = 'prefix_titles.json'
    with open(filename, 'w') as json_file:
        json.dump(prefix_titles, json_file, indent=4)

    print(f'The dictionary has been saved to {filename}')

if __name__ == '__main__':
    main()
