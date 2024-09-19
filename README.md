# gdrive-testing
This resposity is used for monitoring a user's Google Drive.
We will check if there was a new file added to the Drive.

If we had a new file that is public and under a shared folder, we will modify the file to be private.

# Prerequisites are:

-  Python 3.10.7 or greater
-  The pip package management tool
-  A Google Cloud project.
-  A Google account with Google Drive enabled.


Follow instructions on how to setup the environemnt in -> https://developers.google.com/drive/api/quickstart/python

Enable the API in your project, and set a name for the app using this repository.

Once you have configured the app name in your project, take the credentials downloaded from https://developers.google.com/drive/api/quickstart/python#authorize_credentials_for_a_desktop_application and save them in the directory as credentials.json.

# Components

`authenticate_to_drive()`

This funciton is based on Google's documentation and will authenticate to the Google Drive API.

`get_start_page_token()`

This function was taken from Google's documentation and is used for getting the starting page token for monitoring changes.

`check_for_changes()`

This function gets a service and a saved starting page token and checks for changed in Google Drive files. Based on the https://developers.google.com/drive/api/reference/rest/v3/changes/list api.

`check_if_object_is_public()`

This function checks if a Google Drive Object ID (File, or Folder) had public permissions (permission type 'anyone')

`remove_public_permission()`

This function gets a fileID, and will remove the public permissions of 'anyone' returning it to private.

# Running the program

Authenticate to your browser with the user of the Google Drive you want to monitor.

Then, simply use `python3 ./gdrive_monitor.py` 

Once the script is run, and you have an authenticated used, you will need to approve the the app scope.
![unverified_continue](https://github.com/user-attachments/assets/6a3a6942-9fe5-45e5-a8a0-53d9eb95cb6f)

![unverified_g_app](https://github.com/user-attachments/assets/bb5475d3-9b53-41ab-b764-c611eb8fb8f8)

After you approve it, you should see something like this:

![authenticated](https://github.com/user-attachments/assets/81867069-d15b-4282-a674-747c319a72a1)



# Flow of the program

1. The program starts with the authentication and creation of credentials to a file called `token.json` 
2. Then the starting page token is obtained to read the changes of the google drive with `changes.list`, and take the field values of `id, name, parents, version`
3. Loop over the changes and check for a `file` change (although folder changes are also considered a file change)
4. Given a file change, we extract the file name, file ID, file version and parents.
5. In order to determine if the file is a new file we look at the file version. More on the file version can be found here -> https://developers.google.com/drive/api/reference/rest/v3/files#:~:text=with%20keepForever%20enabled.-,version,-string%20(int64 . Based on experimenting, we noticed that a file is uploaded on version 1, and if its part of a shared folder it will automatically become shared as version 2 (although some edge cases)
6. Once we determine if the file is new, we check if it's public, and if it's parent is public.
7. If both are public, meaning we have a new file that's public in a shared folder, we will remove the files permissions of being public.
8. Otherwise, we will print relevant messages.

# Getting the default sharing settings of files in the google account

Unfortunately, we found that general sharing settings can be found in admin console such as in this answer -> https://support.google.com/a/answer/60781 .
Therefore, in order to determine a default setting wasnt found, but can be iterated for folders.


# Possible Attack surfaces with the API

1. Possible abuse of other apps, finding the default apps used by a user with https://developers.google.com/drive/api/reference/rest/v3/apps/list
2. Hidden persistence with a hidden drive with https://developers.google.com/drive/api/reference/rest/v3/drives/hide
3. In addition, if an attacker gets the refresh token, there might be misuse without needing to authenticate again.
