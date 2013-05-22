import copy
import urlparse
import json

import requests

from keystoneclient.v2_0 import users
from keystoneclient.openstack.common.apiclient import client as api_client
from keystoneclient.openstack.common.apiclient import fake_client
from tests import utils


class UserTests(utils.TestCase):
    def setUp(self):
        super(UserTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_USERS = {
            "users": {
                "values": [
                    {
                        "email": "None",
                        "enabled": True,
                        "id": 1,
                        "name": "admin",
                    },
                    {
                        "email": "None",
                        "enabled": True,
                        "id": 2,
                        "name": "demo",
                    },
                ]
            }
        }

    def test_create(self):
        req_body = {
            "user": {
                "name": "gabriel",
                "password": "test",
                "tenantId": 2,
                "email": "test@example.com",
                "enabled": True,
            }
        }
        resp_body = {
            "user": {
                "name": "gabriel",
                "enabled": True,
                "tenantId": 2,
                "id": 3,
                "password": "test",
                "email": "test@example.com",
            }
        }
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request(
            'POST',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        user = self.client.users.create(req_body['user']['name'],
                                        req_body['user']['password'],
                                        req_body['user']['email'],
                                        tenant_id=req_body['user']['tenantId'],
                                        enabled=req_body['user']['enabled'])
        self.assertTrue(isinstance(user, users.User))
        self.assertEqual(user.id, 3)
        self.assertEqual(user.name, "gabriel")
        self.assertEqual(user.email, "test@example.com")

    def test_delete(self):
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": "",
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'DELETE',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/1'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.users.delete(1)

    def test_get(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps({
                'user': self.TEST_USERS['users']['values'][0],
            })
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'GET',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/1'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        u = self.client.users.get(1)
        self.assertTrue(isinstance(u, users.User))
        self.assertEqual(u.id, 1)
        self.assertEqual(u.name, 'admin')

    def test_list(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_USERS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'GET',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        user_list = self.client.users.list()
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_limit(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_USERS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'GET',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users?limit=1'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        user_list = self.client.users.list(limit=1)
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_marker(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_USERS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'GET',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users?marker=foo'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        user_list = self.client.users.list(marker='foo')
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_limit_marker(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_USERS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request(
            'GET',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users?marker=foo&limit=1'),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        user_list = self.client.users.list(limit=1, marker='foo')
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_update(self):
        req_1 = {
            "user": {
                "id": 2,
                "email": "gabriel@example.com",
                "name": "gabriel",
            }
        }
        req_2 = {
            "user": {
                "id": 2,
                "password": "swordfish",
            }
        }
        req_3 = {
            "user": {
                "id": 2,
                "tenantId": 1,
            }
        }
        req_4 = {
            "user": {
                "id": 2,
                "enabled": False,
            }
        }

        # Keystone basically echoes these back... including the password :-/
        resp_1 = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(req_1)
        })
        resp_2 = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(req_2)
        })
        resp_3 = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(req_3)
        })
        resp_4 = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(req_4)
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_1)
        self.add_request(
            'PUT',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/2'),
            **kwargs).AndReturn((resp_1))
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_2)
        self.add_request(
            'PUT',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/2/OS-KSADM/password'),
            **kwargs).AndReturn((resp_2))
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_3)
        self.add_request(
            'PUT',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/2/OS-KSADM/tenant'),
            **kwargs).AndReturn((resp_3))
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_4)
        self.add_request(
            'PUT',
            urlparse.urljoin(self.TEST_URL, 'v2.0/users/2/OS-KSADM/enabled'),
            **kwargs).AndReturn((resp_4))
        self.mox.ReplayAll()

        user = self.client.users.update(2,
                                        name='gabriel',
                                        email='gabriel@example.com')
        user = self.client.users.update_password(2, 'swordfish')
        user = self.client.users.update_tenant(2, 1)
        user = self.client.users.update_enabled(2, False)

    def test_update_own_password(self):
        req_body = {
            'user': {
                'password': 'ABCD', 'original_password': 'DCBA'
            }
        }
        resp_body = {
            'access': {}
        }
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body)
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request(
            'PATCH',
            urlparse.urljoin(self.TEST_URL, 'v2.0/OS-KSCRUD/users/123'),
            **kwargs).AndReturn((resp))

        self.mox.ReplayAll()

        self.client.users.update_own_password('DCBA', 'ABCD')
