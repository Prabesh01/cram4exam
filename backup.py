# 0 */6 * * * /home/prabesh/cram4exam/venv/bin/python3 /home/prabesh/cram4exam/backup.py

import requests

from datetime import datetime as dt
timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
dropbox_path = f'/ratta/db-{timestamp}.sqlite3'

import os, sys
basedir=os.path.dirname(os.path.abspath(__file__))

from dotenv import load_dotenv
load_dotenv(basedir+'/.env')
access_token=os.getenv('dropbox_access_token')

to_backup=basedir+"/db.sqlite3"

import hashlib
last_md5_file="/tmp/ratta.last"
def get_file_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # Read in 64k chunks
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

last_md5=""
if os.path.exists(last_md5_file): last_md5=open(last_md5_file).read()
current_md5= get_file_checksum(to_backup)
if current_md5==last_md5: 
    print("nth changed. skipping backup")
    sys.exit(0)
with open(last_md5_file, 'w') as f: f.write(current_md5)

with open(to_backup,'rb') as f:
    data=f.read()

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/octet-stream',
    'Dropbox-API-Arg': '{"path": "%s", "mode": "add", "autorename": false, "mute": false, "strict_conflict": false}' % dropbox_path
}

url = 'https://content.dropboxapi.com/2/files/upload'
response = requests.post(url, headers=headers, data=data)
print(response.text)
