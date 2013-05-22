from keystoneclient.openstack.common.apiclient import client as api_client

from keystoneclient.auth import keystone
from keystoneclient import utils


@utils.arg('--user-name', metavar='<user-name>', default='admin', dest='user',
           help='The name of the user to be created (default="admin").')
@utils.arg('--pass', metavar='<password>', required=True, dest='passwd',
           help='The password for the new user.')
@utils.arg('--role-name', metavar='<role-name>', default='admin', dest='role',
           help='The name of the role to be created and granted to the user '
           '(default="admin").')
@utils.arg('--tenant-name', metavar='<tenant-name>', default='admin',
           dest='tenant',
           help='The name of the tenant to be created (default="admin").')
def do_bootstrap(kc, args):
    """Grants a new role to a new user on a new tenant, after creating each."""
    tenant = kc.tenants.create(tenant_name=args.tenant)
    role = kc.roles.create(name=args.role)
    user = kc.users.create(name=args.user, password=args.passwd, email=None)
    kc.roles.add_user_role(user=user, role=role, tenant=tenant)

    # verify the result
    http_client = kc.http_client
    auth_plugin = keystone.KeystoneV2AuthPlugin(
        username=args.user,
        password=args.passwd,
        tenant_name=args.tenant,
        auth_url=http_client.auth_plugin.opts["auth_url"])
    auth_plugin.authenticate(http_client)
