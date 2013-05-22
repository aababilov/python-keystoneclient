# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
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

"""
Command-line interface to the OpenStack Identity API.
"""

from __future__ import print_function

import argparse
import getpass
import os
import sys

import keystoneclient

from keystoneclient.openstack.common.apiclient.auth import base as auth_base
from keystoneclient.openstack.common.apiclient.auth import response
from keystoneclient.openstack.common.apiclient import client as api_client
from keystoneclient.openstack.common.apiclient import exceptions as exc
from keystoneclient import utils
from keystoneclient.v2_0 import shell as shell_v2_0
from keystoneclient.generic import shell as shell_generic
from keystoneclient.contrib.bootstrap import shell as shell_bootstrap


def positive_non_zero_float(argument_value):
    if argument_value is None:
        return None
    try:
        value = float(argument_value)
    except ValueError:
        msg = "%s must be a float" % argument_value
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % argument_value
        raise argparse.ArgumentTypeError(msg)
    return value


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


class OpenStackIdentityShell(object):

    def __init__(self, parser_class=argparse.ArgumentParser):
        self.parser_class = parser_class

    def get_base_parser(self):
        parser = self.parser_class(
            prog='keystone',
            description=__doc__.strip(),
            epilog='See "keystone help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h',
                            '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--version',
                            action='version',
                            version=keystoneclient.__version__,
                            help="Shows the client version and exits")

        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--timeout',
                            default=600,
                            type=positive_non_zero_float,
                            metavar='<seconds>',
                            help="Set request timeout (in seconds)")

        parser.add_argument('--os-region-name',
                            metavar='<region-name>',
                            default=env('OS_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME]')
        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-identity-api-version',
                            metavar='<identity-api-version>',
                            default=env('OS_IDENTITY_API_VERSION',
                                        'KEYSTONE_VERSION'),
                            help='Defaults to env[OS_IDENTITY_API_VERSION]'
                                 ' or 2.0')
        parser.add_argument('--os_identity_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-cacert',
                            metavar='<ca-certificate>',
                            default=env('OS_CACERT', default=None),
                            help='Specify a CA bundle file to use in '
                                 'verifying a TLS (https) server certificate. '
                                 'Defaults to env[OS_CACERT]')
        parser.add_argument('--os_cacert',
                            help=argparse.SUPPRESS)

        parser.add_argument('--insecure',
                            default=False,
                            action="store_true",
                            help='Explicitly allow keystoneclient to perform '
                                 '"insecure" TLS (https) requests. The '
                                 'server\'s certificate will not be verified '
                                 'against any certificate authorities. This '
                                 'option should be used with caution.')

        parser.add_argument('--os-cert',
                            metavar='<certificate>',
                            default=env('OS_CERT'),
                            help='Defaults to env[OS_CERT]')
        parser.add_argument('--os_cert',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-key',
                            metavar='<key>',
                            default=env('OS_KEY'),
                            help='Defaults to env[OS_KEY]')
        parser.add_argument('--os_key',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-cache',
                            default=env('OS_CACHE', default=False),
                            action='store_true',
                            help='Use the auth token cache. '
                                 'Defaults to env[OS_CACHE]')
        parser.add_argument('--os_cache',
                            help=argparse.SUPPRESS)

        parser.add_argument('--force-new-token',
                            default=False,
                            action="store_true",
                            dest='force_new_token',
                            help="If the keyring is available and in use, "
                                 "token will always be stored and fetched "
                                 "from the keyring until the token has "
                                 "expired. Use this option to request a "
                                 "new token and replace the existing one "
                                 "in the keyring.")

        parser.add_argument('--stale-duration',
                            metavar='<seconds>',
                            default=response.STALE_TOKEN_DURATION,
                            dest='stale_duration',
                            help="Stale duration (in seconds) used to "
                                 "determine whether a token has expired "
                                 "when retrieving it from keyring. This "
                                 "is useful in mitigating process or "
                                 "network delays. Default is %s seconds." % (
                            response.STALE_TOKEN_DURATION))

        auth_base.discover_auth_systems()
        auth_base.load_auth_system_opts(parser)
        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '2.0': shell_v2_0,
            }[version]
        except KeyError:
            actions_module = shell_v2_0

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, shell_generic)
        self._find_actions(subparsers, shell_bootstrap)
        self._find_actions(subparsers, self)
        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)
            subparser.add_argument('-h', '--help', action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            group = subparser.add_argument_group(title='Arguments')
            for (args, kwargs) in arguments:
                group.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)

        # build available subcommands based on version
        api_version = options.os_identity_api_version
        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if not argv or options.help:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        try:
            self.auth_plugin = auth_base.load_plugin_from_args(args)
        except exc.AuthPluginOptionsMissing as ex:
            raise exc.CommandError(ex)
        if args.os_cert and args.os_key:
            cert = (args.os_cert, args.os_key)
        else:
            cert = args.os_cert or None
        verify = args.os_cacert if args.os_cacert else not args.insecure
        self.http_client = api_client.HTTPClient(
            auth_plugin=self.auth_plugin,
            cert=cert,
            verify=verify,
            http_log_debug=args.debug,
            timeout=args.timeout)

        if utils.isunauthenticated(args.func):
            client_class = shell_generic.CLIENT_CLASS
        else:
            api_version = options.os_identity_api_version
            client_class = self.get_api_class(api_version)
        self.cs = client_class(http_client=self.http_client)
        try:
            args.func(self.cs, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Identity credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

    def get_api_class(self, version):
        try:
            return {
                "2.0": shell_v2_0.CLIENT_CLASS,
            }[version]
        except KeyError:
            return shell_v2_0.CLIENT_CLASS

    def do_bash_completion(self, args):
        """
        Prints all of the commands and options to stdout.
        The keystone.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackIdentityShell().main(sys.argv[1:])

    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
