# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sample application that demonstrates different ways of fetching
URLS on App Engine
"""

import logging
import os
import urllib
import json

# [START urllib2-imports]
import urllib2
# [END urllib2-imports]
import httplib2

from google.appengine.api import app_identity
# [START urlfetch-imports]
from google.appengine.api import urlfetch
# [END urlfetch-imports]
from oauth2client import service_account
from apiclient.discovery import build as discovery_build
from apiclient.http import MediaFileUpload
from apiclient.errors import HttpError

import webapp2


def GetAuthorizedHttpForGcsApi():
    # Acquire credentials from service account key file 
    service_account_keyfile = './appenginedefault-yaoliu.json'
    scopes = (
        'https://www.googleapis.com/auth/cloud-platform', 
        'https://www.googleapis.com/auth/devstorage.read_write',
    )
    creds = service_account.ServiceAccountCredentials.from_json_keyfile_name(
        service_account_keyfile,
        scopes)    
    
    return creds.authorize(httplib2.Http())    


class UrlLibFetchHandler(webapp2.RequestHandler):
    """ Demonstrates an HTTP query using urllib2"""

    def get(self):
        # [START urllib-get]
        url = 'http://www.google.com/humans.txt'
        try:
            result = urllib2.urlopen(url)
            self.response.write(result.read())
        except urllib2.URLError:
            logging.exception('Caught exception fetching url')
        # [END urllib-get]


class UrlFetchHandler(webapp2.RequestHandler):
    """ Demonstrates an HTTP query using urlfetch"""

    def get(self):

        # [START urlfetch-get]
        url = 'http://www.google.com/humans.txt'
        try:
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                self.response.write(result.content)
            else:
                self.response.status_code = result.status_code
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
        # [END urlfetch-get]


class UrlPostHandler(webapp2.RequestHandler):
    """ Demonstrates an HTTP POST form query using urlfetch"""

    form_fields = {
        'first_name': 'Albert',
        'last_name': 'Johnson',
    }

    def get(self):
        # [START urlfetch-post]
        try:
            form_data = urllib.urlencode(UrlPostHandler.form_fields)
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            result = urlfetch.fetch(
                url='http://localhost:8080/submit_form',
                payload=form_data,
                method=urlfetch.POST,
                headers=headers)
            self.response.write(result.content)
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
        # [END urlfetch-post]

class GcsObjectListUrlFetch(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://www.googleapis.com/storage/v1/b/{0}/o'.format(bucket_name)
        headers = {'authorization': 'Bearer ...'} # Redacted access token
        result = urlfetch.fetch(
            url=url,
            headers=headers)
        self.response.write(result.content)

class GcsObjectInsertUrlFetch(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://storage.googleapis.com/upload/storage/v1/b/{0}/o?uploadType=multipart&alt=json'.format(bucket_name)
        headers = {
            'authorization': 'Bearer ...', # Redacted access token
            'Content-Type': 'multipart/related; boundary=foo_bar_baz',
            # 'Content-Length': '655360'
        }
        upload_content = 'yaoliu1  ' * 1024 * 64
        payload = '''--foo_bar_baz
Content-Type: application/json
MIME-Version: 1.0

{{"metadata": {{"foo": "bar"}}, "name": "yao-test-gcs"}}
--foo_bar_baz
Content-Type: text/plain
MIME-Version: 1.0
Content-Transfer-Encoding: binary

{0}

--foo_bar_baz--
'''.format(upload_content)
        result = urlfetch.fetch(
            url=url,
            payload=payload,
            method=urlfetch.POST,
            headers=headers)
        self.response.write(result.content)    

class GcsObjectListHttplib2(webapp2.RequestHandler):
    def get(self):
        http = GetAuthorizedHttpForGcsApi()
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://www.googleapis.com/storage/v1/b/{0}/o'.format(bucket_name)
        (resp, content) = http.request(
            uri=url,
            method="GET")
        self.response.write(content)

class GcsObjectInsertHttplib2(webapp2.RequestHandler):
    def get(self):
        http = GetAuthorizedHttpForGcsApi()
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://storage.googleapis.com/upload/storage/v1/b/{0}/o?uploadType=multipart&alt=json'.format(bucket_name)
        headers = {
            'Content-Type': 'multipart/related; boundary=foo_bar_baz',
            # 'Content-Length': '655360'
        }
        upload_content = 'yaoliu2  ' * 1024 * 64
        payload = '''--foo_bar_baz
Content-Type: application/json
MIME-Version: 1.0

{{"metadata": {{"foo": "bar"}}, "name": "yao-test-gcs"}}
--foo_bar_baz
Content-Type: text/plain
MIME-Version: 1.0
Content-Transfer-Encoding: binary

{0}

--foo_bar_baz--
'''.format(upload_content)
        (resp, content) = http.request(
            uri=url,
            method="POST",
            body=payload,
            headers=headers)
        self.response.write(content)


class GcsObjectInsertApiClient(webapp2.RequestHandler):
    def get(self):
        http = GetAuthorizedHttpForGcsApi()
        service = discovery_build('storage', 'v1', http=http)

        print 'Building upload request...'
        file_to_upload = './yao-test-gcs.txt'
        media = MediaFileUpload(file_to_upload, resumable=True)
        if not media.mimetype():
            media = MediaFileUpload(filename, 'text/plain', resumable=True)        
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        object_name = 'yao-test-gcs'
        request = service.objects().insert(bucket=bucket_name, name=object_name, media_body=media)
        
        print 'Uploading file: %s to bucket: %s object: %s ' % (file_to_upload, bucket_name, object_name)
        RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)


        response = None
        counter = 1
        while response is None:
            error = None
            try:
                print ('Upload round ', counter)
                progress, response = request.next_chunk()
                if progress:
                    print('Upload %d%%' % (100 * progress.progress()))
                counter += 1
            except HttpError, err:
                error = err
                if err.resp.status < 500:
                    raise
            except RETRYABLE_ERRORS, err:
                error = err


        print '\nUpload complete!'
        print self.response.write(json.dumps(response, indent=2))           


class SubmitHandler(webapp2.RequestHandler):
    """ Handler that receives UrlPostHandler POST request"""
    def post(self):
        self.response.out.write((self.request.get('first_name')))


app = webapp2.WSGIApplication([
    ('/', UrlLibFetchHandler),
    ('/url_fetch', UrlFetchHandler),
    ('/url_post', UrlPostHandler),
    ('/submit_form', SubmitHandler),
    ('/gcs_list_object_urlfetch', GcsObjectListUrlFetch),
    ('/gcs_insert_object_urlfetch', GcsObjectInsertUrlFetch),
    ('/gcs_list_object_httplib2', GcsObjectListHttplib2),
    ('/gcs_insert_object_httplib2', GcsObjectInsertHttplib2),
    ('/gcs_insert_object_apiclient', GcsObjectInsertApiClient),
], debug=True)
