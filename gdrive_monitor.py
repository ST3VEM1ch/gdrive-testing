import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly",  # Read metadata
    "https://www.googleapis.com/auth/drive.file"  # Manage files opened or created by the app
]


def authenticate_to_drive():
    """
    This function will perform an authentication to Google drive using OAuth with a prompt for app consent.
    :return: a service object to interact with the Drive API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)
        return service

    except HttpError as error:
        print(f"An error occurred: {error}")
        exit(1)


def get_object_permissions(service, object_id):
    """
    Gets a Google Drive object id and returns its permissions
    :param service: Resource object for interacting with an API
    :param object_id: the object of which we want the permissions
    :return: The list of permissions
    """
    return service.permissions().list(fileId=object_id).execute()


def check_if_object_is_public(service, object_id):
    """
    This functions checks if a given object is public and has 'anyone' in the permissions
    :param service: Resource object for interacting with an API
    :param object_id: the file or folder object we want to check
    :return: True if the object is public, False otherwise
    """
    permissions = get_object_permissions(service, object_id)
    for perm in permissions['permissions']:
        if perm['type'] == 'anyone':
            return True
    return False


def remove_public_permission(service, file_id, file_name):
    """
    This function deletes any publie access permissions
    :param service: Resource object for interacting with an API
    :param file_id: the file id we want to make private
    :return:
    """""
    permissions = get_object_permissions(service, file_id)
    for perm in permissions:
        if isinstance(perm, dict) and perm.get('type') == 'anyone':
            print(f"[!!] Removing public permission from file: {file_name}")
            service.permissions().delete(fileId=file_id, permissionId=perm['id']).execute()


def get_start_page_token(service):
    """
    Get the starting page token for monitoring changes. (Taken from Google documentation)
    :param service: Resource object for interacting with an API
    :return:
    """
    response = service.changes().getStartPageToken().execute()
    return response.get('startPageToken')


def check_for_changes(service, saved_start_page_token):
    """
    This function gets a service and a saved starting page token and checks for changed in Google Drive files.
    :param service: Resource object for interacting with an API
    :param saved_start_page_token: A token of an authenticated session
    :return: the latest page token to save for the next run
    """""
    page_token = saved_start_page_token
    while page_token:
        response = service.changes().list(
            pageToken=page_token,
            spaces='drive',
            fields="nextPageToken, changes(file(id, name, parents, version))"
        ).execute()

        for change in response['changes']:
            print(f"[+] Checking for changes in Google Drive...\n")
            if 'file' in change:
                file_id = change['file']['id']
                file_name = change['file']['name']
                file_version = int(change['file']['version'])
                parents_id = change['file']['parents'][0]
                print(f"[+] Change detected in file: {file_name} (ID: {file_id}), parents: {parents_id}, "
                      f"version {file_version}\n")
                print(f"[+] Checking if the file is new and needs analysis...\n")
                # On research found that version starts with 2, but just in case there might be 0 - 3
                # A small file version indicates a newer file
                if file_version < 3:
                    is_file_public = check_if_object_is_public(service, file_id)
                    is_parent_public = check_if_object_is_public(service, parents_id)
                    if is_file_public and is_parent_public:
                        print(f"[!] New file {file_name} is public under a public parent folder.\n")
                        remove_public_permission(service, file_id, file_name)
                    elif is_parent_public:
                        print(f"[!] New file {file_name} is private under a public parent folder.\n")
                    elif is_file_public:
                        print(f"[!] New file {file_name} is public under a private parent folder.\n")
                    else:
                        # this might be just undet the drive
                        print(f"[!] New file {file_name} is private under a private parent.\n")

                else:
                    print(f"[-] File {file_name} isn't new.")

        page_token = response.get('nextPageToken', None)

    # Return the latest page token to save for the next run
    return response.get('newStartPageToken', None)


def main():
    service = authenticate_to_drive()

    start_page_token = get_start_page_token(service)

    while True:
        new_start_page_token = check_for_changes(service, start_page_token)

        if new_start_page_token:
            start_page_token = new_start_page_token  # Save the new token for future use




if __name__ == "__main__":
    main()
