import os
import pickle

import yaml
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

__all__ = ['GdriveException', 'Gdrive']

from const import RESOURCE_ROOT


class GdriveException(Exception):
    pass


AUTH_PERMISSION = ['https://www.googleapis.com/auth/drive']
GDRIVE_DIR = os.path.join(RESOURCE_ROOT, 'gdrive')
if not os.path.exists(GDRIVE_DIR):
    os.mkdir(GDRIVE_DIR)
ROOT_ID = '1pF86ZrtkinrNLEbHzkmPOMy-9U1eT_uO'
PATH_YML_ID = '16ztOnnnrUX_Rr8lSx2k3uGTZ1S79v8BW'
PATH_YML = os.path.join(GDRIVE_DIR, 'path.yml')


class Gdrive:
    TOKEN_PICKLE = os.path.join(GDRIVE_DIR, 'token.pickle')
    CREDENTIALS_JSON = os.path.join(GDRIVE_DIR, 'credentials.json')

    def __connect(self):
        creds = None
        if os.path.exists(self.TOKEN_PICKLE):
            with open(self.TOKEN_PICKLE, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_JSON, AUTH_PERMISSION)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def refresh_yaml(self, upload):
        path_root = Path(self.get_name(ROOT_ID), ROOT_ID, 'folder')
        queue = [path_root]

        def append_all_file_in_folder(_head):
            page_token = None
            while True:
                response = self.service.files().list(q=f"'{_head.file_id}' in parents and trashed = false",
                                                     spaces='drive',
                                                     fields='nextPageToken, files(id, name, mimeType)',
                                                     pageToken=page_token).execute()
                for file in response.get('files', []):
                    file_id = file.get('id')
                    file_name = file.get('name')
                    file_type = file.get('mimeType')

                    # we do not need this many file type, just folder or file
                    if file_type == 'application/vnd.google-apps.folder':
                        file_type = 'folder'
                    else:
                        file_type = 'file'

                    new_path = Path(file_name, file_id, file_type)
                    _head.child.append(new_path)

                    # if this file is a folder, then recursively listing
                    if file_type == 'folder':
                        queue.append(new_path)

                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

        while len(queue) > 0:
            head = queue[0]
            queue.pop(0)
            append_all_file_in_folder(head)

        path_root.dump_yaml(PATH_YML, force=True)
        if upload:
            self.update_file(PATH_YML, PATH_YML_ID)
        return path_root

    def __init__(self):
        self.service = None
        self.__connect()
        if not os.path.exists(PATH_YML):
            self.get_file(PATH_YML_ID, PATH_YML)
        self.path = Path.from_yaml(PATH_YML)

    def update_path_yml(self, upload=False):
        pass

    def create_file(self, local_path, remote_name, remote_parent_id=None):
        file_metadata = {'name': remote_name}
        if remote_parent_id is not None:
            file_metadata['parents'] = [remote_parent_id]
        media = MediaFileUpload(local_path, mimetype='text/plain')
        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        return file.get('id')

    def create_folder(self, remote_name, remote_parent_id=None):
        file_metadata = {
            'name': remote_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if remote_parent_id is not None:
            file_metadata['parents'] = [remote_parent_id]

        file = self.service.files().create(body=file_metadata,
                                           fields='id').execute()
        return file.get('id')

    def update_file(self, local_path, remote_id):
        media = MediaFileUpload(local_path, mimetype='text/plain')
        self.service.files().update(fileId=remote_id,
                                    media_body=media).execute()

    def get_file(self, file_id, out=None, force=False):
        request = self.service.files().get_media(fileId=file_id)
        if out is None:
            out = self.get_name(file_id)
        if os.path.exists(out) and not force:
            raise GdriveException(f'file "{out}" already exists')
        with open(out, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f'Download {int(status.progress() * 100)}%.')

    def get_name(self, file_id):
        return self.service.files().get(fileId=file_id, fields='name').execute().get('name')


"""
Support a convenient way to access gdrive data.
Restriction: folder/files in the root folder should have the same format of usual file system, 
i.e., no file with same name in a same directory.
Local cache helps user access file by ID directly instead of look dir by dir through gdrive API.
Local cache is stored in yaml.

API

1. A way to initialize the yaml.

2. When create/upload a file/dir, update yaml

3. When rename a file/dir, update yaml


"""


class Path:
    @classmethod
    def from_yaml(cls, path_yml):
        d = yaml.load(open(path_yml, 'r'), Loader=yaml.Loader)
        assert len(d) == 1
        k, v = next(iter(d.items()))
        return cls.from_kv(k, v)

    @classmethod
    def from_kv(cls, key, val):
        head_path = cls(key, val['id'], val['type'])
        if val['type'] == 'folder':
            for k, v in val['child'].items():
                head_path.child.append(cls.from_kv(k, v))
        return head_path

    def __init__(self, name, file_id, file_type):
        self.name = name
        self.file_id = file_id
        self.file_type = file_type
        if file_type == 'folder':
            self.child = []
        else:
            self.child = None

    def dump(self):
        key = self.name
        val = {'id': self.file_id, 'type': self.file_type}
        if self.child is not None:
            val['child'] = {}
            for c in self.child:
                k, v = c.dump()
                val['child'][k] = v
        return key, val

    def dump_yaml(self, out, force=False):
        if os.path.exists(out) and not force:
            raise GdriveException(f'file "{out}" already exists')
        with open(out, 'w') as f:
            k, v = self.dump()
            f.write(yaml.dump({k: v}))

    def __str__(self):
        return str(self.dump())

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)})'
