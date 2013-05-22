import copy
import urlparse
import json

import requests

from keystoneclient.openstack.common.apiclient import client as api_client
from keystoneclient.openstack.common.apiclient import exceptions
from keystoneclient.openstack.common.apiclient import fake_client
from keystoneclient.v2_0 import tenants
from tests import utils


class TenantTests(utils.TestCase):
    def setUp(self):
        super(TenantTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_TENANTS = {
            "tenants": {
                "values": [
                    {
                        "enabled": True,
                        "description": "A description change!",
                        "name": "invisible_to_admin",
                        "id": 3,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "demo",
                        "id": 2,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "admin",
                        "id": 1,
                    }
                ],
                "links": [],
            },
        }

    def test_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "Like tenant 9, but better.",
                "enabled": True
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": True,
                "id": 4,
                "description": "Like tenant 9, but better.",
            }
        }
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request('POST',
                         urlparse.urljoin(self.TEST_URL, 'v2.0/tenants'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant = self.client.tenants.create(req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "Like tenant 9, but better.")

    def test_duplicate_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "The duplicate tenant.",
                "enabled": True
            },
        }
        resp_body = {
            "error": {
                "message": "Conflict occurred attempting to store project.",
                "code": 409,
                "title": "Conflict",
            }
        }
        resp = fake_client.TestResponse({
            "status_code": 409,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request('POST',
                         urlparse.urljoin(self.TEST_URL, 'v2.0/tenants'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        def create_duplicate_tenant():
            self.client.tenants.create(req_body['tenant']['name'],
                                       req_body['tenant']['description'],
                                       req_body['tenant']['enabled'])

        self.assertRaises(exceptions.Conflict, create_duplicate_tenant)

    def test_delete(self):
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": "",
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('DELETE',
                         urlparse.urljoin(self.TEST_URL, 'v2.0/tenants/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.tenants.delete(1)

    def test_get(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps({
                'tenant': self.TEST_TENANTS['tenants']['values'][2],
            }),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL, 'v2.0/tenants/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        t = self.client.tenants.get(1)
        self.assertTrue(isinstance(t, tenants.Tenant))
        self.assertEqual(t.id, 1)
        self.assertEqual(t.name, 'admin')

    def test_list(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_TENANTS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL, 'v2.0/tenants'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list()
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_limit(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_TENANTS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants?limit=1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(limit=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_marker(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_TENANTS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants?marker=1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(marker=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_limit_marker(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_TENANTS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants?marker=1&limit=1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(limit=1, marker=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_update(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": 4,
                "description": "I changed you!",
            },
        }
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request('POST',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant = self.client.tenants.update(req_body['tenant']['id'],
                                            req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "I changed you!")
        self.assertFalse(tenant.enabled)

    def test_update_empty_description(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "",
                "enabled": False,
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": 4,
                "description": "",
            },
        }
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        self.add_request('POST',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        tenant = self.client.tenants.update(req_body['tenant']['id'],
                                            req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "")
        self.assertFalse(tenant.enabled)

    def test_add_user(self):
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('PUT',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.tenants.add_user('4', 'foo', 'barrr')

    def test_remove_user(self):
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.tenants.remove_user('4', 'foo', 'barrr')

    def test_tenant_add_user(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('PUT',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.add_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))

    def test_tenant_remove_user(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        resp = fake_client.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.remove_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))
