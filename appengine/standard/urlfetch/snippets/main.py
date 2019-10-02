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

from google.appengine.api import app_identity
# [START urlfetch-imports]
from google.appengine.api import urlfetch
# [END urlfetch-imports]
import webapp2


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

class GcsObjectList(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://www.googleapis.com/storage/v1/b/{0}/o'.format(bucket_name)
        headers = {'authorization': 'Bearer ...'} # Redacted access token
        result = urlfetch.fetch(
            url=url,
            headers=headers)
        self.response.write(result.content)

class GcsObjectInsert(webapp2.RequestHandler):
    def get(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        url = 'https://storage.googleapis.com/upload/storage/v1/b/{0}/o?uploadType=multipart'.format(bucket_name)
        headers = {
            'authorization': 'Bearer ...', # Redacted access token
            'Content-Type': 'multipart/related; boundary=foo_bar_baz',
            'Content-Length': '655360'
        }
        upload_content = 'yeah' * 1024 * 64
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


class SubmitHandler(webapp2.RequestHandler):
    """ Handler that receives UrlPostHandler POST request"""

    def post(self):
        self.response.out.write((self.request.get('first_name')))


app = webapp2.WSGIApplication([
    ('/', UrlLibFetchHandler),
    ('/url_fetch', UrlFetchHandler),
    ('/url_post', UrlPostHandler),
    ('/submit_form', SubmitHandler),
    ('/gcs_get_object', GcsObjectList),
    ('/gcs_insert_object', GcsObjectInsert)
], debug=True)
