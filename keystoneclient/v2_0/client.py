# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import logging

from keystoneclient.openstack.common.apiclient import client
from keystoneclient.openstack.common.apiclient import exceptions
from keystoneclient.v2_0 import ec2
from keystoneclient.v2_0 import endpoints
from keystoneclient.v2_0 import roles
from keystoneclient.v2_0 import services
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import tokens
from keystoneclient.v2_0 import users


_logger = logging.getLogger(__name__)


class Client(client.BaseClient):
    """Client for the OpenStack Keystone v2.0 API.

    Example:: FIXME

        >>> from keystoneclient.openstack.common.apiclient import client as api_client
        >>> from keystoneclient.v2_0 import client
        >>> http_client = api_client.HTTPClient()
        >>> admin_client = client.Client(
        ...     token='12345secret7890',
        ...     endpoint='http://localhost:35357/v2.0')
        >>> keystone.tenants.list()

    """
    service_type = "identity"
    endpoint_type = "adminURL"

    def __init__(self, **kwargs):
        """Initialize a new client for the Keystone v2.0 API."""
        super(Client, self).__init__(**kwargs)
        self.endpoints = endpoints.EndpointManager(self)
        self.roles = roles.RoleManager(self)
        self.services = services.ServiceManager(self)
        self.tenants = tenants.TenantManager(self)
        self.tokens = tokens.TokenManager(self)
        self.users = users.UserManager(self)

        # extensions
        self.ec2 = ec2.CredentialsManager(self)
