import copy
import json

import mock
import requests

from keystoneclient.apiclient import client as api_client
from keystoneclient.apiclient import exceptions
from keystoneclient.apiclient import fake_client

from keystoneclient.auth import keystone

from tests.v3 import utils


class KeystoneAuthPluginV2Test(utils.TestCase):

    def test_authenticate(self):
        http_client = api_client.HTTPClient(None)
        mock_request = mock.Mock()
        mock_request.return_value = fake_client.TestResponse({
            "status_code": 200,
            "text": {"access": {"token": {"id": "123"}}}
        })
        successful_tests = [
            {
                "kwargs": ["tenant_id", "token", "auth_url"],
                "data": {
                    "auth": {
                        "token": {"id": "token"}, "tenantId": "tenant_id"
                    },
                },
            },
            {
                "kwargs": ["tenant_name", "token", "auth_url"],
                "data": {
                    "auth": {
                        "token": {"id": "token"}, "tenantName": "tenant_name"
                    },
                },
            },
            {
                "kwargs": ["username", "password", "tenant_name", "auth_url"],
                "data": {
                    "auth": {
                        "tenantName": "tenant_name",
                        "passwordCredentials": {
                            "username": "username",
                            "password": "password",
                        },
                    },
                },
            },
        ]
        with mock.patch("requests.Session.request", mock_request):
            for test in successful_tests:
                kwargs = dict((k, k) for k in test["kwargs"])
                auth = keystone.KeystoneAuthPluginV2(**kwargs)
                http_client.auth_plugin = auth
                http_client.authenticate()
                requests.Session.request.assert_called_with(
                    "POST",
                    "auth_url/tokens",
                    headers=mock.ANY,
                    allow_redirects=True,
                    data=json.dumps(test["data"]),
                    verify=mock.ANY)

            auth = keystone.KeystoneAuthPluginV3(
                password="password",
                tenant_name="tenant_name",
                auth_url="auth_url")
            http_client.auth_plugin = auth
            self.assertRaises(exceptions.AuthPluginOptionsMissing,
                              http_client.authenticate)


class KeystoneAuthPluginV3Test(utils.TestCase):

    def setUp(self):
        super(KeystoneAuthPluginV3Test, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "token": {
                "methods": [
                    "token",
                    "password"
                ],

                "expires_at": "2020-01-01T00:00:10.000123Z",
                "project": {
                    "domain": {
                        "id": self.TEST_DOMAIN_ID,
                        "name": self.TEST_DOMAIN_NAME
                    },
                    "id": self.TEST_TENANT_ID,
                    "name": self.TEST_TENANT_NAME
                },
                "user": {
                    "domain": {
                        "id": self.TEST_DOMAIN_ID,
                        "name": self.TEST_DOMAIN_NAME
                    },
                    "id": self.TEST_USER,
                    "name": self.TEST_USER
                },
                "issued_at": "2013-05-29T16:55:21.468960Z",
                "catalog": self.TEST_SERVICE_CATALOG
            },
        }
        self.TEST_REQUEST_BODY = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "domain": {
                                "name": self.TEST_DOMAIN_NAME
                            },
                            "name": self.TEST_USER,
                            "password": self.TEST_TOKEN
                        }
                    }
                },
                "scope": {
                    "project": {
                        "id": self.TEST_TENANT_ID
                    },
                }
            }
        }
        self.TEST_REQUEST_HEADERS = {
            'Content-Type': 'application/json',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_RESPONSE_HEADERS = {
            'X-Subject-Token': self.TEST_TOKEN
        }
        self.TEST_REQUEST_BASE = copy.copy(self.TEST_REQUEST_BASE)
        self.TEST_REQUEST_BASE["allow_redirects"] = True

    def _authenticate(self, **kwargs):
        auth = keystone.KeystoneAuthPluginV3(**kwargs)
        self.http_client.auth_plugin = auth
        self.http_client.authenticate()

    def test_authenticate_success(self):
        TEST_TOKEN = "abcdef"
        self.TEST_RESPONSE_HEADERS['X-Subject-Token'] = TEST_TOKEN
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(
            user_id=self.TEST_USER,
            password=self.TEST_TOKEN,
            project_id=self.TEST_TENANT_ID,
            auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         TEST_TOKEN)

    def test_authenticate_failure(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        ident['password']['user']['password'] = 'bad_key'
        resp = fake_client.TestResponse({
            "status_code": 401,
            "text": json.dumps({
                "unauthorized": {
                    "message": "Unauthorized",
                    "code": "401",
                },
            }),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        # Workaround for issue with assertRaises on python2.6
        # where with assertRaises(exceptions.Unauthorized): doesn't work
        # right
        def client_create_wrapper():
            self._authenticate(user_domain_name=self.TEST_DOMAIN_NAME,
                               username=self.TEST_USER,
                               password="bad_key",
                               project_id=self.TEST_TENANT_ID,
                               auth_url=self.TEST_URL)

        self.assertRaises(exceptions.Unauthorized, client_create_wrapper)

    def test_authenticate_success_domain_username_password_scoped(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(user_domain_name=self.TEST_DOMAIN_NAME,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(
            self.http_client.auth_plugin.access_info.management_url[0],
            self.TEST_RESPONSE_DICT["token"]["catalog"][3]
            ['endpoints'][2]["url"])
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_userid_password_domain_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER

        scope = self.TEST_REQUEST_BODY['auth']['scope']
        del scope['project']
        scope['domain'] = {}
        scope['domain']['id'] = self.TEST_DOMAIN_ID

        token = self.TEST_RESPONSE_DICT['token']
        del token['project']
        token['domain'] = {}
        token['domain']['id'] = self.TEST_DOMAIN_ID
        token['domain']['name'] = self.TEST_DOMAIN_NAME

        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS

        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(user_id=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           domain_id=self.TEST_DOMAIN_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.domain_id,
                         self.TEST_DOMAIN_ID)
        self.assertEqual(
            self.http_client.auth_plugin.access_info.management_url[0],
            self.TEST_RESPONSE_DICT["token"]["catalog"][3]
            ['endpoints'][2]["url"])
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_userid_password_project_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']['user']['domain']
        del ident['password']['user']['name']
        ident['password']['user']['id'] = self.TEST_USER

        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS

        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(user_id=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.tenant_id,
                         self.TEST_TENANT_ID)
        self.assertEqual(
            self.http_client.auth_plugin.access_info.management_url[0],
            self.TEST_RESPONSE_DICT["token"]["catalog"][3]
            ['endpoints'][2]["url"])
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_password_unscoped(self):
        del self.TEST_RESPONSE_DICT['token']['catalog']
        del self.TEST_REQUEST_BODY['auth']['scope']
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(user_domain_name=self.TEST_DOMAIN_NAME,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertFalse('catalog' in self.http_client.auth_plugin.access_info.
                         service_catalog.catalog)

    def test_authenticate_success_token_domain_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN

        scope = self.TEST_REQUEST_BODY['auth']['scope']
        del scope['project']
        scope['domain'] = {}
        scope['domain']['id'] = self.TEST_DOMAIN_ID

        token = self.TEST_RESPONSE_DICT['token']
        del token['project']
        token['domain'] = {}
        token['domain']['id'] = self.TEST_DOMAIN_ID
        token['domain']['name'] = self.TEST_DOMAIN_NAME

        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(token=self.TEST_TOKEN,
                           domain_id=self.TEST_DOMAIN_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.domain_id,
                         self.TEST_DOMAIN_ID)
        self.assertEqual(
            self.http_client.auth_plugin.access_info.management_url[0],
            self.TEST_RESPONSE_DICT["token"]["catalog"][3]
            ['endpoints'][2]["url"])
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_token_project_scoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(token=self.TEST_TOKEN,
                           project_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.tenant_id,
                         self.TEST_TENANT_ID)
        self.assertEqual(
            self.http_client.auth_plugin.access_info.management_url[0],
            self.TEST_RESPONSE_DICT["token"]["catalog"][3]
            ['endpoints'][2]["url"])
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])

    def test_authenticate_success_token_unscoped(self):
        ident = self.TEST_REQUEST_BODY['auth']['identity']
        del ident['password']
        ident['methods'] = ['token']
        ident['token'] = {}
        ident['token']['id'] = self.TEST_TOKEN
        del self.TEST_REQUEST_BODY['auth']['scope']
        del self.TEST_RESPONSE_DICT['token']['catalog']
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
            "headers": self.TEST_RESPONSE_HEADERS,
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY, sort_keys=True)
        self.add_request('POST',
                         self.TEST_URL + "/auth/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self._authenticate(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(self.http_client.auth_plugin.access_info.auth_token,
                         self.TEST_RESPONSE_HEADERS["X-Subject-Token"])
        self.assertFalse('catalog' in self.http_client.auth_plugin.access_info.
                         service_catalog.catalog)
