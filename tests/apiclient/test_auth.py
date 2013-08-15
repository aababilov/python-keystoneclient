# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import argparse

import fixtures
import mock

from stevedore import extension

from keystoneclient.apiclient import auth

from tests import utils


class BaseFakePlugin(auth.BaseAuthPlugin):
    def _do_authenticate(self, http_client):
        pass

    def token_and_endpoint(self, endpoint_type, service_type):
        pass


class GlobalFunctionsTest(utils.TestCase):

    def test_load_auth_system_opts(self):
        self.useFixture(fixtures.MonkeyPatch(
            "os.environ",
            {"OS_TENANT_NAME": "fake-project",
            "OS_USERNAME": "fake-username"}))
        parser = argparse.ArgumentParser()
        auth.load_auth_system_opts(parser)
        options = parser.parse_args(
            ["--os-auth-url=fake-url", "--os_auth_system=fake-system"])
        self.assertTrue(options.os_tenant_name, "fake-project")
        self.assertTrue(options.os_username, "fake-username")
        self.assertTrue(options.os_auth_url, "fake-url")
        self.assertTrue(options.os_auth_system, "fake-system")


class MockEntrypoint(object):
    def __init__(self, name, plugin):
        self.name = name
        self.plugin = plugin


class AuthPluginTest(utils.TestCase):
    @mock.patch.object(extension.ExtensionManager, "map")
    def test_auth_system_success(self, mock_mgr_map):
        """Test that we can authenticate using the auth system."""
        class FakePlugin(BaseFakePlugin):
            def authenticate(self, http_client):
                return "fake-success"

        mock_mgr_map.side_effect = (
            lambda func: func(MockEntrypoint("fake", FakePlugin)))

        auth.discover_auth_systems()
        plugin = auth.load_plugin("fake")
        self.assertEqual(plugin.authenticate(None), "fake-success")

    @mock.patch.object(extension.ExtensionManager, "map")
    def test_discover_auth_system_options(self, mock_mgr_map):
        """Test that we can load the auth system options."""
        class FakePlugin(BaseFakePlugin):
            @classmethod
            def add_opts(cls, parser):
                parser.add_argument('--auth_system_opt',
                                    default=False,
                                    action='store_true',
                                    help="Fake option")

        mock_mgr_map.side_effect = (
            lambda func: func(MockEntrypoint("fake", FakePlugin)))

        parser = argparse.ArgumentParser()
        auth.discover_auth_systems()
        auth.load_auth_system_opts(parser)
        opts, _args = parser.parse_known_args(['--auth_system_opt'])

        self.assertTrue(opts.auth_system_opt)

    @mock.patch.object(extension.ExtensionManager, "map")
    def test_parse_auth_system_options(self, mock_mgr_map):
        """Test that we can parse the auth system options."""
        class FakePlugin(BaseFakePlugin):
            opt_names = ["fake_argument"]

        mock_mgr_map.side_effect = (
            lambda func: func(MockEntrypoint("fake", FakePlugin)))

        auth.discover_auth_systems()
        plugin = auth.load_plugin("fake")

        plugin.parse_opts([])
        self.assertIn("fake_argument", plugin.opts)
