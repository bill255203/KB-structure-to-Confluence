import functions_framework
import sys
import json
from bs4 import BeautifulSoup
import copy
from apiclient import errors, discovery
from oauth2client import client,tools,file
from operator import itemgetter, attrgetter
import requests
from requests.auth import HTTPBasicAuth
from google.cloud import storage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from oauth2client.client import GoogleCredentials

storage_client = storage.Client()
BUCKET_NAME = 'kb-confluence'

def read_json_from_gcs(bucket_name, file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    return json.loads(blob.download_as_text())

def write_json_to_gcs(bucket_name, file_name, data):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(data), content_type='application/json')

prefix_titles = read_json_from_gcs(BUCKET_NAME, 'prefix_titles.json')
created_pages = read_json_from_gcs(BUCKET_NAME, 'created_pages.json')
confluence_secret = read_json_from_gcs(BUCKET_NAME, 'confluence_secret.json')

# Extracting the necessary data from your secrets
API_TOKEN = confluence_secret["API_TOKEN"]
SPACE_ID = confluence_secret["SPACE_ID"]
PARENT_ID = confluence_secret["PARENT_ID"]
EMAIL = confluence_secret["EMAIL"]
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

SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
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
@functions_framework.http
def main(request):
    service_account_info = read_json_from_gcs(BUCKET_NAME, 'client_secret.json')
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    print(service_account_info,credentials)
    service = build('drive', 'v3', credentials=credentials)
    print(f"Remaining Pages: {remaining_pages}")
    
    folder_id = '0AJEo31zRZZG7Uk9PVA'
    foldername = ''
    try:
        folder = service.drives().get(driveId=folder_id, fields='name').execute()
        foldername = folder['name']
        drivetype = 'Shared Drive'
        print(f"Folder ID {folder_id} is a Google Drive Folder called: {foldername}")
    except HttpError as error:
        print(f'An error occurred: {error}')
        foldername = ''

    if not foldername:
        print('No folder name found.')
        exit()
    folders_only = False
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
    print(f"Final prefix titles: {prefix_titles}")
    write_json_to_gcs(BUCKET_NAME, 'prefix_titles.json', prefix_titles)
    write_json_to_gcs(BUCKET_NAME, 'created_pages.json', created_pages)

    return 'Finished all execution'
