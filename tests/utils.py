import time

import mock
import mox
import testtools

from keystoneclient import access
from keystoneclient.apiclient import client as api_client
from keystoneclient.apiclient import fake_client
from keystoneclient.auth import keystone
from keystoneclient.v2_0 import client


class TestCase(testtools.TestCase):
    TEST_DOMAIN_ID = '1'
    TEST_DOMAIN_NAME = 'aDomain'
    TEST_TENANT_ID = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'
    TEST_USER_ID = '123'
    TEST_ROOT_SERVICE_URL = 'http://127.0.0.1:5000/'
    TEST_SERVICE_URL = '%s%s' % (TEST_ROOT_SERVICE_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')
    TEST_ROOT_URL = TEST_ROOT_ADMIN_URL
    TEST_URL = TEST_ADMIN_URL
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    TEST_SERVICE_CATALOG = [{
        "endpoints": [{
            "adminURL": "http://cdn.admin-nets.local:8774/v1.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:8774/v1.0",
            "publicURL": "http://cdn.admin-nets.local:8774/v1.0/"
        }],
        "type": "nova_compat",
        "name": "nova_compat"
    }, {
        "endpoints": [{
            "adminURL": "http://nova/novapi/admin",
            "region": "RegionOne",
            "internalURL": "http://nova/novapi/internal",
            "publicURL": "http://nova/novapi/public"
        }],
        "type": "compute",
        "name": "nova"
    }, {
        "endpoints": [{
            "adminURL": "http://glance/glanceapi/admin",
            "region": "RegionOne",
            "internalURL": "http://glance/glanceapi/internal",
            "publicURL": "http://glance/glanceapi/public"
        }],
        "type": "image",
        "name": "glance"
    }, {
        "endpoints": [{
            "adminURL": "http://127.0.0.1:35357/v2.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:5000/v2.0",
            "publicURL": "http://127.0.0.1:5000/v2.0"
        }],
        "type": "identity",
        "name": "keystone"
    }, {
        "endpoints": [{
            "adminURL": "http://swift/swiftapi/admin",
            "region": "RegionOne",
            "internalURL": "http://swift/swiftapi/internal",
            "publicURL": "http://swift/swiftapi/public"
        }],
        "type": "object-store",
        "name": "swift"
    }]

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        auth_plugin = keystone.KeystoneAuthPluginV2(
            username=self.TEST_USER,
            token=self.TEST_TOKEN,
            tenant_name=self.TEST_TENANT_NAME,
            auth_url=self.TEST_URL)
        auth_plugin.access_info = access.AccessInfo.factory(None, {
            "access": {
                "user": {
                    "name": self.TEST_USER,
                    "id": self.TEST_USER_ID,
                },
                "token": {
                    "id": self.TEST_TOKEN,
                },
                "serviceCatalog": self.TEST_SERVICE_CATALOG,
            },
        })
        self.http_client = api_client.HTTPClient(auth_plugin=auth_plugin)
        self.http_client.user_agent = "python-keystoneclient"
        self.client = client.Client(http_client=self.http_client)

        self.request_patcher = mock.patch.object(
            self.http_client.http,
            'request',
            self.mox.CreateMockAnything())
        self.time_patcher = mock.patch.object(time, 'time',
                                              lambda: 1234)
        self.request_patcher.start()
        self.time_patcher.start()

    def tearDown(self):
        self.request_patcher.stop()
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(TestCase, self).tearDown()

    def add_request(self, *args, **kwargs):
        return self.http_client.http.request(*args, **kwargs)


class UnauthenticatedTestCase(testtools.TestCase):
    """Class used as base for unauthenticated calls."""
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    def setUp(self):
        super(UnauthenticatedTestCase, self).setUp()
        self.http_client = api_client.HTTPClient(auth_plugin=None)
        self.http_client.user_agent = "python-keystoneclient"
        self.mox = mox.Mox()
        self.request_patcher = mock.patch.object(
            self.http_client.http, 'request', self.mox.CreateMockAnything())
        self.time_patcher = mock.patch.object(time, 'time',
                                              lambda: 1234)
        self.request_patcher.start()
        self.time_patcher.start()

    def tearDown(self):
        self.request_patcher.stop()
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(UnauthenticatedTestCase, self).tearDown()

    def add_request(self, *args, **kwargs):
        return self.http_client.http.request(*args, **kwargs)


TestResponse = fake_client.TestResponse
