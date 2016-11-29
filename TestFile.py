from __future__ import print_function
import os

from apiclient import discovery
import httplib2
from oauth2client import file
from oauth2client import client
from oauth2client import tools
import argparse
import sys

# parser = argparse.ArgumentParser(description='Process something.')
# parser.add_argument('integers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')
#
# args = parser.parse_args()
# print(args.accumulate(args.integers))


# Google drive API Uploading/Downloading

try:
	import argparse

	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

SCOPES = 'https://www.googleapis.com/auth/drive.file'

# Setup/retrieve credentials if already exists.
home_dir = os.path.expanduser('~')
credentials_dir = os.path.join(home_dir, '.credentials')
if not credentials_dir:
	os.mkdir(credentials_dir)
credentials_path = os.path.join(credentials_dir, 'google-drive-API-store.json')

# Get credentials from store
store = file.Storage(credentials_path)
credentials = store.get()

if not credentials or credentials.invalid:
	flow = client.flow_from_clientsecrets('client_secret.json', scope=SCOPES)

	credentials = tools.run_flow(flow, store, flags) \
		if flags else tools.run_flow(flow, store)

google_drive = discovery.build('drive', 'v3', http=credentials.authorize(httplib2.Http()))

folder_metadata = {
	'name': 'timelapse',
	'mimeType': 'application/vnd.google-apps.folder'
}
folder = google_drive.service.files().create(body=folder_metadata, fields='id').execute()
print('Folder ID: %s' % file.get('id'))


# Upload files to google drive
files = (
	('hello.txt', None),
	('hello.txt', 'application/vnd.google-apps.document')
)

for filename, mimeType in files:
	metadata = {'name': filename}
	if mimeType:
		metadata['mimeType'] = mimeType
	result = google_drive.files().create(body=metadata, media_body=filename).execute()
	if result:
		print('Uploaded "%s" (%s)' % (filename, result['mimeType']))

if result:
	MIMETYPE = 'application/pdf'
	data = google_drive.files().export(fileId=result['id'], mimeType=MIMETYPE).execute()
	if data:
		fn = '%s.pdf' % os.path.splitext(filename)[0]
		with open(fn, 'wb') as fh:
			fh.write(data)
		print('Downloaded "%s" (%s)' % (fn, MIMETYPE))
