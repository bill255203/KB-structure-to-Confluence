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

root_title = "bill1"
root_value = """<a href="https://drive.google.com/drive/u/0/folders/0ANbyjco9413kUk9PVA">KB here</a>"""
prefix_titles, created_pages, remaining_pages = None, None, None
confluence_secret = read_json_from_gcs(BUCKET_NAME, 'confluence_secret.json')
API_TOKEN = confluence_secret["API_TOKEN"]
SPACE_ID = confluence_secret["SPACE_ID"]
PARENT_ID = confluence_secret["PARENT_ID"]
EMAIL = confluence_secret["EMAIL"]

# Here are the create, update, and delete functions for Confluence pages
def create_confluence_page(title, parent_id, body_value, prefixed_title):
    global prefix_titles
    global created_pages
    global remaining_pages
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
    try:
        response = requests.request("POST", url, data=payload, headers=headers, auth=auth)
        print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        response_data = json.loads(response.text)  # Parse the JSON response
        page_id = response_data.get('id')  # Get the 'id' field from the response
        version_number = response_data.get('version', {}).get('number')
        print(page_id)
        created_pages[title] = [page_id, version_number, prefixed_title]
        prefix_titles[prefixed_title] = True
        return page_id
    except Exception as e:
        print(f"An error occurred: {e}")
    
def update_confluence_page(title, body_value, update_id, version_number, prefixed_title):
    global prefix_titles
    global created_pages
    global remaining_pages
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
    try:
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
        print(f"In progress pages after Update: {remaining_pages}")
        return page_id
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_page(delete_title, delete_id, delete_prefixed_title):
    global prefix_titles
    global created_pages
    global remaining_pages
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
def get_file_type(item):
    if 'mimeType' in item:
        mime_type = item['mimeType']
        parts = mime_type.split('.')
        if parts[0] == 'application/vnd' and len(parts) > 2:
            # Extract the key word (like 'audio', 'document', etc.)
            key_word = parts[-1]
            return "(" + key_word + ")"
        else:
            return ""
    else:
        return ""
def manage_confluence_page(original_title, prefixed_title, parent_page_id, body_value, created_pages, prefix_titles):
    """
    Manages the creation or updating of a Confluence page.

    Parameters:
    original_title (str): The original title of the page.
    prefixed_title (str): The prefixed title of the page.
    parent_page_id (int): The ID of the parent page.
    body_value (str): The content of the page.
    created_pages (dict): A dictionary tracking created pages.
    prefix_titles (dict): A dictionary tracking pages with prefixed titles.
    """
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
    return new_parent_page_id

def process_root_folders(service, drive_id, confluence_parent_id):
    """
    Process the root folders in a Google Drive and create or update corresponding Confluence pages.

    Args:
        service: Google Drive API service instance.
        drive_id (str): ID of the Google Drive.
        confluence_parent_id (int): ID of the parent Confluence page.
    """
    global prefix_titles, created_pages
    page_token = None

    while True:
        try:
            param = {'pageToken': page_token} if page_token else {}
            query = f"'{drive_id}' in parents"
            results = service.files().list(
                q=query,
                driveId=drive_id,
                corpora='drive',
                includeItemsFromAllDrives='false',
                supportsAllDrives='true',
                fields="nextPageToken, files(id, name, parents, webViewLink, iconLink, mimeType)"
            ).execute()

            items = results.get('files', [])
            items.sort(key=lambda item: item['name'])
            file_list_html = ""  # HTML string to list files

            # Iterate over items in the root folder
            for item in items:
                item_id = item['id']
                item_name = item['name']
                mime_type = get_file_type(item)
                item_link = item['webViewLink']

                # Process files and folders differently
                if item['mimeType'] != 'application/vnd.google-apps.folder':
                    # Add file to the HTML list
                    file_list_html += f"<span><a href='{item_link}'>{mime_type} {item_name}</a></span>"
                else:
                    # Process sub-folder
                    subfolder_html = f"<span><a href='{item_link}'>{mime_type} {item_name}</a></span>"
                    subfolder_body_value = str(BeautifulSoup(subfolder_html, 'html.parser'))
                    subfolder_title = f"KB_{item_name}"
                    new_confluence_parent_id = manage_confluence_page(item_name, subfolder_title, confluence_parent_id, subfolder_body_value, created_pages, prefix_titles)
                    
                    # Recursive call to process sub-folder
                    process_child_folders(service, item_id, drive_id, new_confluence_parent_id, item_name)

            # Process files in the root folder
            if file_list_html:
                file_list_body_value = str(BeautifulSoup(file_list_html, 'html.parser'))
                file_page_title = "KB_files"
                if file_page_title in created_pages:
                    update_id, version_number = int(created_pages[file_page_title][0]), created_pages[file_page_title][1]
                    update_confluence_page(file_page_title, file_list_body_value, update_id, version_number + 1, file_page_title)
                else:
                    create_confluence_page(file_page_title, confluence_parent_id, file_list_body_value, file_page_title)

            # Check if there are more pages of items
            page_token = results.get('nextPageToken')
            if not page_token:
                break

        except errors.HttpError as error:
            print(f'An error occurred: {error}')
            break

def process_child_folders(service, parent_folder_id, drive_id, confluence_parent_id, current_folder_name):
    """
    Process Google Drive folders and files, and create or update corresponding Confluence pages.

    Args:
        service: Google Drive API service instance.
        parent_folder_id (str): ID of the parent folder in Google Drive.
        drive_id (str): ID of the Google Drive.
        confluence_parent_id (int): ID of the parent Confluence page.
        current_folder_name (str): Name of the current Google Drive folder.
    """
    global prefix_titles, created_pages
    page_token = None

    while True:
        try:
            param = {'pageToken': page_token} if page_token else {}
            query = f"'{parent_folder_id}' in parents"
            results = service.files().list(
                q=query,
                driveId=drive_id,
                corpora='drive',
                includeItemsFromAllDrives='false',
                supportsAllDrives='true',
                fields="nextPageToken, files(id, name, parents, webViewLink, iconLink, mimeType)"
            ).execute()

            items = results.get('files', [])
            items.sort(key=lambda item: item['name'])

            has_file = False
            file_list_html = "<ul>"  # HTML string to list files

            # Iterate over items in the current folder
            for item in items:
                item_id = item['id']
                item_name = item['name']
                mime_type = get_file_type(item)
                item_link = item['webViewLink']

                # Process files and folders differently
                if item['mimeType'] != 'application/vnd.google-apps.folder':
                    # Add file to the HTML list
                    file_list_html += f"<li><a href='{item_link}'>{mime_type} {item_name}</a></li>"
                    has_file = True
                else:
                    # Process sub-folder
                    subfolder_html = f"<li><a href='{item_link}'>{mime_type} {item_name}</a></li>"
                    subfolder_body_value = str(BeautifulSoup(subfolder_html, 'html.parser'))
                    subfolder_title = f"{current_folder_name}_{item_name}"
                    new_confluence_parent_id = manage_confluence_page(item_name, subfolder_title, confluence_parent_id, subfolder_body_value, created_pages, prefix_titles)
                    
                    # Recursive call to process sub-folder
                    process_child_folders(service, item_id, drive_id, new_confluence_parent_id, item_name)

            # Process files in the current folder
            if has_file:
                file_list_body_value = str(BeautifulSoup(file_list_html + "</ul>", 'html.parser'))
                file_page_title = f"{current_folder_name}_files"
                prefixed_file_page_title = f"{current_folder_name}_{file_page_title}"
                manage_confluence_page(file_page_title, prefixed_file_page_title, confluence_parent_id, file_list_body_value, created_pages, prefix_titles)

            # Check if there are more pages of items
            page_token = results.get('nextPageToken')
            if not page_token:
                break

        except errors.HttpError as error:
            print(f'An error occurred: {error}')
            break

@functions_framework.http
def main(request):
    service_account_info = read_json_from_gcs(BUCKET_NAME, 'client_secret.json')
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    print(service_account_info,credentials)
    service = build('drive', 'v3', credentials=credentials)
    global prefix_titles
    global created_pages
    global remaining_pages
    prefix_titles = read_json_from_gcs(BUCKET_NAME, 'prefix_titles.json')
    created_pages = read_json_from_gcs(BUCKET_NAME, 'created_pages.json')
    remaining_pages = created_pages.copy()
    print(f"Init Pages: {remaining_pages}")
    folder_id = '0AJEo31zRZZG7Uk9PVA'
    foldername = ''
    try:
        folder = service.drives().get(driveId=folder_id, fields='name').execute()
        foldername = folder['name']
        print(f"Folder ID {folder_id} is a Google Drive Folder called: {foldername}")
    except HttpError as error:
        print(f'An error occurred: {error}')
        foldername = ''
    if not foldername:
        print('No folder name found.')
        exit()
    print('Building folder structure for {0}'.format(folder['name']))
    if root_title in created_pages:
        update_id, version_number = int(created_pages[root_title][0]), created_pages[root_title][1]
        parent_id = update_confluence_page(root_title, root_value, update_id, version_number + 1, root_title)
    else:
        parent_id = create_confluence_page(root_title, PARENT_ID, root_value, root_title)
    process_root_folders(service, folder_id, parent_id)
    print(f"Pages need to delete: {remaining_pages}")
    for delete_title, info in remaining_pages.items():
        delete_id, version_number, delete_prefixed_title = int(info[0]), info[1], info[2]
        delete_page(delete_title, delete_id, delete_prefixed_title)
    
    print(f"Final Created Pages: {created_pages}")   
    print(f"Final prefix titles: {prefix_titles}")
    write_json_to_gcs(BUCKET_NAME, 'prefix_titles.json', prefix_titles)
    write_json_to_gcs(BUCKET_NAME, 'created_pages.json', created_pages)
    return 'Finished all execution'