# Test python file
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def google_auth():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    drive = GoogleDrive(gauth)

    return drive

