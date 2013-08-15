# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import mock

import requests

from keystoneclient import exceptions
from keystoneclient import httpclient
from tests import utils


FAKE_RESPONSE = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
MOCK_REQUEST = mock.Mock(return_value=(FAKE_RESPONSE))


def get_client(token="", endpoint=""):
    cl = httpclient.HTTPClient(token=token, endpoint=endpoint)
    return cl


def get_authed_client():
    return get_client(
        token="token",
        endpoint="http://127.0.0.1:5000")


class FakeLog(object):
    def __init__(self):
        self.warn_log = str()
        self.debug_log = str()

    def warn(self, msg=None, *args, **kwargs):
        self.warn_log = "%s\n%s" % (self.warn_log, (msg % args))

    def debug(self, msg=None, *args, **kwargs):
        self.debug_log = "%s\n%s" % (self.debug_log, (msg % args))


class ClientTest(utils.TestCase):

    def test_unauthorized_client_requests(self):
        cl = get_client()
        self.assertRaises(exceptions.AuthorizationFailure, cl.get, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.post, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.put, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.delete, '/hi')

    def test_get(self):
        cl = get_authed_client()

        with mock.patch.object(requests.Session, "request", MOCK_REQUEST):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp = cl.get("/hi")
                body = resp.json()
                headers = {"X-Auth-Token": "token",
                           "User-Agent": cl.http_client.user_agent}
                MOCK_REQUEST.assert_called_with(
                    "GET",
                    "http://127.0.0.1:5000/hi",
                    headers=headers,
                    **self.TEST_REQUEST_BASE)
                # Automatic JSON parsing
                self.assertEqual(body, {"hi": "there"})

    def test_get_error_with_plaintext_resp(self):
        cl = get_authed_client()

        fake_err_response = utils.TestResponse({
            "status_code": 400,
            "text": 'Some evil plaintext string',
        })
        err_MOCK_REQUEST = mock.Mock(return_value=(fake_err_response))

        with mock.patch.object(requests.Session, "request", err_MOCK_REQUEST):
            self.assertRaises(exceptions.BadRequest, cl.get, '/hi')

    def test_get_error_with_json_resp(self):
        cl = get_authed_client()
        err_response = {
            "error": {
                "code": 400,
                "title": "Error title",
                "message": "Error message string"
            }
        }
        fake_err_response = utils.TestResponse({
            "status_code": 400,
            "text": json.dumps(err_response),
            "headers": {"Content-Type": "application/json"},
        })
        err_MOCK_REQUEST = mock.Mock(return_value=(fake_err_response))

        with mock.patch.object(requests.Session, "request", err_MOCK_REQUEST):
            exc_raised = False
            try:
                cl.get('/hi')
            except exceptions.BadRequest as exc:
                exc_raised = True
                self.assertEqual(exc.message, "Error message string")
            self.assertTrue(exc_raised, 'Exception not raised.')

    def test_post(self):
        cl = get_authed_client()

        with mock.patch.object(requests.Session, "request", MOCK_REQUEST):
            cl.post("/hi", json=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.http_client.user_agent
            }
            MOCK_REQUEST.assert_called_with(
                "POST",
                "http://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **self.TEST_REQUEST_BASE)
