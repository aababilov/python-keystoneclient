# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
# Copyright 2013 Spanish National Research Council.
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

from keystoneclient.openstack.common.apiclient.auth import base
from keystoneclient.openstack.common.apiclient import exceptions


logger = logging.getLogger(__name__)


class KeystoneV2AuthPlugin(base.BaseAuthPlugin):
    auth_system = "keystone"
    opt_names = [
        "username",
        "password",
        "tenant_id",
        "tenant_name",
        "token",
        "auth_url",
    ]

    def sufficient_options(self):
        if not (self.opts.get("auth_url") and
                ((self.opts.get("username") and self.opts.get("password")) or
                 self.opts.get("token"))):
            raise exceptions.AuthPluginOptionsMissing(
                [opt
                 for opt in ("auth_url", "username", "password", "token")
                 if not self.opts.get(opt)])

    def _do_authenticate(self, http_client):
        if self.opts.get("token"):
            params = {"auth": {"token": {"id": self.opts.get("token")}}}
        else:
            params = {
                "auth": {
                    "passwordCredentials": {
                        "username": self.opts.get("username"),
                        "password": self.opts.get("password"),
                    }
                }
            }
        if self.opts.get("tenant_id"):
            params["auth"]["tenantId"] = self.opts.get("tenant_id")
        elif self.opts.get("tenant_name"):
            params["auth"]["tenantName"] = self.opts.get("tenant_name")
        try:
            body = http_client.request(
                "POST",
                http_client.concat_url(self.opts.get("auth_url"), "/tokens"),
                allow_redirects=True,
                json=params).json()
        except ValueError as ex:
            raise exceptions.AuthorizationFailure(ex)
        http_client.auth_response = body
