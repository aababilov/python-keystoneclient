import copy
import urlparse
import json

import requests

from keystoneclient.v2_0 import services
from keystoneclient.openstack.common.apiclient import client as api_client
from keystoneclient.openstack.common.apiclient import fake_client
from tests import utils


class ServiceTests(utils.TestCase):
    def setUp(self):
        super(ServiceTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': api_client.HTTPClient.user_agent,
        }
        self.TEST_SERVICES = {
            "OS-KSADM:services": {
                "values": [
                    {
                        "name": "nova",
                        "type": "compute",
                        "description": "Nova-compatible service.",
                        "id": 1
                    },
                    {
                        "name": "keystone",
                        "type": "identity",
                        "description": "Keystone-compatible service.",
                        "id": 2
                    },
                ],
            },
        }

    def test_create(self):
        req_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
            }
        }
        resp_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
                "id": 3,
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
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/services'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        service = self.client.services.create(
            req_body['OS-KSADM:service']['name'],
            req_body['OS-KSADM:service']['type'],
            req_body['OS-KSADM:service']['description'])
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.id, 3)
        self.assertEqual(service.name, req_body['OS-KSADM:service']['name'])

    def test_delete(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": "",
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/services/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.services.delete(1)

    def test_get(self):
        test_services = self.TEST_SERVICES['OS-KSADM:services']['values'][0]
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps({'OS-KSADM:service': test_services}),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/services/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        service = self.client.services.get(1)
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.id, 1)
        self.assertEqual(service.name, 'nova')
        self.assertEqual(service.type, 'compute')

    def test_list(self):
        resp = fake_client.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_SERVICES),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        self.add_request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/services'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        service_list = self.client.services.list()
        [self.assertTrue(isinstance(r, services.Service))
         for r in service_list]
