from __future__ import print_function
import httplib2
import os
import sys

from apiclient import discovery
from googleapiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


class GoogleDriveManager:
	def __init__(self):
		"""
		Initialize drive manager. Authenticate user if needed.
		Init does everything needed to get other
		"""
		try:
			import argparse
			self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
		except ImportError:
			self.flags = None

		# If modifying these scopes, delete your previously saved credentials
		# at ~/.credentials/drive-python-quickstart.json
		self.SCOPES = 'https://www.googleapis.com/auth/drive'
		self.CLIENT_SECRET_FILE = 'client_secret.json'
		self.APPLICATION_NAME = 'Timelapse'

		# Try creating drive after verifying credentials
		credentials = self._get_credentials()
		http = credentials.authorize(httplib2.Http())
		self.drive = discovery.build('drive', 'v3', http=http)

	def _get_credentials(self):
		"""Gets valid user credentials from storage.

		If nothing has been stored, or if the stored credentials are invalid,
		the OAuth2 flow is completed to obtain the new credentials.

		Returns:
			Credentials, the obtained credential.
		"""
		# Create a directory at ~/.credentials if does not exist.
		home_dir = os.path.expanduser('~')
		credential_dir = os.path.join(home_dir, '.credentials')
		if not os.path.exists(credential_dir):
			os.makedirs(credential_dir)

		# Assume there's a file named 'drive-python-quickstart.json'
		credential_path = os.path.join(credential_dir, 'drive-python-timelapse.json')
		store = Storage(credential_path)
		credentials = store.get()  # Get credentials from the Store created with the given path

		# If file does not exist or token has expired/invalid, auth user again
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
			flow.user_agent = self.APPLICATION_NAME
			if self.flags:
				credentials = tools.run_flow(flow, store, self.flags)
			else:  # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
			print('Storing credentials to ' + credential_path)

		return credentials

	# Tries to get the id with the given folder name and returns the files
	def _get_folder_id(self, folder_name, exact=False):
		# Query for searching file. If exact flag is provided, will match for name that matches 100%
		if exact:
			query = "mimeType='application/vnd.google-apps.folder' " \
					"and trashed=false" \
					"and name = '{}'".format(folder_name)
		else:
			query = "mimeType='application/vnd.google-apps.folder' and name contains '{}'".format(folder_name)

		results = self.drive.files().list(
			q=query,
			fields="nextPageToken, files(id, name)"
		).execute()

		items = results.get('files', [])

		for item in items:
			print(item.get('name') + ' ' + item.get('id'))

		if not items:
			return None
		return items[0]['id']

	def upload_file(self, ufile, folder_name=None):
		"""
		Upload a single file to google drive, or to a given folder name if specified.
		If folder does not exist, it will be created.
		:param drive: Authorized service created from apiclient.discovery.build()
		:param ufile: Tuple of file to be uploaded
					with file name as key and mimeType as value eg: ('docs/hello.txt', 'application/vnd.google-apps.document')
		:param folder_name: String name of the desired folder name
		:return: file as a result
		"""
		folder_id = None

		# Get folder_id if needed
		if folder_name:
			folder_id = self._get_folder_id(folder_name, exact=True)
			# If id not available, create a new folder
			if not folder_id:
				metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}

				result = self.drive.files().create(body=metadata, fields='name, id').execute()
				folder_id = result.get('id')
				print('{} ({}) has been created.'.format(result.get('name'), folder_id))

		filename = ufile[0]
		mime_type = ufile[1]

		metadata = {'name': filename}
		if mime_type:
			metadata['mimeType'] = mime_type
		if folder_id:
			metadata['parents'] = [folder_id]

		media = MediaFileUpload(filename,
								mimetype=mime_type,
								resumable=True)

		result = self.drive.files().create(body=metadata,
										media_body=media,
										fields='name, id').execute()
		return result


def main():
	drive_manager = GoogleDriveManager()

	# folder_name = 'timelapse + today date'
	# Upload files to google drive
	ufile = ('hello.txt', 'application/vnd.google-apps.document')
	result = drive_manager.upload_file(ufile=ufile, folder_name='timelapse')

	print('{} ({}) is success fully uploaded.'.format(result.get('name'), result.get('id')))


if __name__ == '__main__':
	main()
