# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import logging
import urlparse

try:
    import keyring
    import pickle
except ImportError:
    keyring = None
    pickle = None

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from keystoneclient import access
from keystoneclient.apiclient import client
from keystoneclient.auth import endpoint as auth_endpoint
from keystoneclient.auth import keystone as auth_keystone


_logger = logging.getLogger(__name__)


class HTTPClient(client.BaseClient):
    """Base class for Keystone clients of different versions.

    Fields and properties:
    * auth_domain_id
    * auth_tenant_id
    * auth_user_id
    * auth_ref
    * auth_token
    * auth_token_from_user
    * auth_url
    * cert
    * debug_log
    * domain_id
    * domain_name
    * force_new_token
    * management_url
    * original_ip
    * password
    * project_domain_id
    * project_domain_name
    * project_id
    * project_name
    * region_name
    * stale_duration
    * timeout
    * use_keyring
    * user_domain_id
    * user_domain_name
    * user_id
    * username
    * verify_cert
    * version
    """

    service_type = "identity"
    endpoint_type = "adminURL"

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, timeout=None,
                 endpoint=None, token=None, cacert=None, key=None,
                 cert=None, insecure=False, original_ip=None, debug=False,
                 auth_ref=None, use_keyring=False, force_new_token=False,
                 stale_duration=None, user_id=None, user_domain_id=None,
                 user_domain_name=None, domain_id=None, domain_name=None,
                 project_id=None, project_name=None, project_domain_id=None,
                 project_domain_name=None,
                 version=None,
                 http_client=None):
        """Construct a new http client

        :param string user_id: User ID for authentication. (optional)
        :param string username: Username for authentication. (optional)
        :param string user_domain_id: User's domain ID for authentication.
                                      (optional)
        :param string user_domain_name: User's domain name for authentication.
                                        (optional)
        :param string password: Password for authentication. (optional)
        :param string domain_id: Domain ID for domain scoping. (optional)
        :param string domain_name: Domain name for domain scoping. (optional)
        :param string project_id: Project ID for project scoping. (optional)
        :param string project_name: Project name for project scoping.
                                    (optional)
        :param string project_domain_id: Project's domain ID for project
                                         scoping. (optional)
        :param string project_domain_name: Project's domain name for project
                                           scoping. (optional)
        :param string auth_url: Identity service endpoint for authorization.
        :param string region_name: Name of a region to select when choosing an
                                   endpoint from the service catalog.
        :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
        :param string endpoint: A user-supplied endpoint URL for the identity
                                service.  Lazy-authentication is possible for
                                API service calls if endpoint is set at
                                instantiation. (optional)
        :param string token: Token for authentication. (optional)
        :param string cacert: Path to the Privacy Enhanced Mail (PEM) file
                              which contains the trusted authority X.509
                              certificates needed to established SSL connection
                              with the identity service. (optional)
        :param string key: Path to the Privacy Enhanced Mail (PEM) file which
                           contains the unencrypted client private key needed
                           to established two-way SSL connection with the
                           identity service. (optional)
        :param string cert: Path to the Privacy Enhanced Mail (PEM) file which
                            contains the corresponding X.509 client certificate
                            needed to established two-way SSL connection with
                            the identity service. (optional)
        :param boolean insecure: Does not perform X.509 certificate validation
                                 when establishing SSL connection with identity
                                 service. default: False (optional)
        :param string original_ip: The original IP of the requesting user
                                   which will be sent to identity service in a
                                   'Forwarded' header. (optional)
        :param boolean debug: Enables debug logging of all request and
                              responses to identity service.
                              default False (optional)
        :param dict auth_ref: To allow for consumers of the client to manage
                              their own caching strategy, you may initialize a
                              client with a previously captured auth_reference
                              (token). If there are keyword arguments passed
                              that also exist in auth_ref, the value from the
                              argument will take precedence.
        :param boolean use_keyring: Enables caching auth_ref into keyring.
                                    default: False (optional)
        :param boolean force_new_token: Keyring related parameter, forces
                                       request for new token.
                                       default: False (optional)
        :param integer stale_duration: Gap in seconds to determine if token
                                       from keyring is about to expire.
                                       default: 30 (optional)
        :param string tenant_name: Tenant name. (optional)
                                   The tenant_name keyword argument is
                                   deprecated, use project_name instead.
        :param string tenant_id: Tenant id. (optional)
                                 The tenant_id keyword argument is
                                 deprecated, use project_id instead.

        """
        self.version = version
        if auth_url:
            auth_url = auth_url.rstrip('/')
        if endpoint:
            endpoint = endpoint.rstrip('/')
        if http_client:
            auth_plugin = http_client.auth_plugin
        elif not auth_url:
            auth_plugin = auth_endpoint.TokenEndpointAuthPlugin(
                token=token,
                endpoint=endpoint)
        elif version == 'v3':
            auth_plugin = auth_keystone.KeystoneAuthPluginV3(
                auth_url=auth_url,
                user_id=user_id,
                username=username,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                password=password,
                domain_id=domain_id,
                domain_name=domain_name,
                project_id=project_id,
                project_name=project_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name,
                token=token
            )
        else:
            auth_plugin = auth_keystone.KeystoneAuthPluginV2(
                auth_url=auth_url,
                user_id=user_id,
                username=username,
                password=password,
                token=token,
                tenant_id=tenant_id,
                tenant_name=tenant_name,
            )
        if endpoint:
            auth_plugin.opts["endpoint"] = endpoint
        if auth_ref:
            auth_plugin.access_info = access.AccessInfo.factory(
                **auth_ref)

        if not http_client:
            if cacert:
                verify = cacert
            else:
                verify = True
            if insecure:
                verify = False
            if cert and key:
                cert = (cert, key,)
            else:
                cert = cert or None
            http_client = client.HTTPClient(
                auth_plugin=auth_plugin,
                timeout=float(timeout) if timeout is not None else None,
                region_name=region_name,
                original_ip=original_ip,
                verify=verify,
                cert=cert,
                debug=debug)
            http_client.user_agent = "python-keystoneclient"
        super(HTTPClient, self).__init__(http_client=http_client)

        # keyring setup
        if use_keyring and keyring is None:
            _logger.warning('Failed to load keyring modules.')
        self.use_keyring = use_keyring and keyring is not None

        self.force_new_token = force_new_token
        self.stale_duration = stale_duration or access.STALE_TOKEN_DURATION
        self.stale_duration = int(self.stale_duration)

    @property
    def debug_log(self):
        return self.http_client.debug

    @property
    def auth_plugin(self):
        return self.http_client.auth_plugin

    @auth_plugin.setter
    def auth_plugin(self, value):
        self.http_client.auth_plugin = value

    @property
    def timeout(self):
        return self.http_client.timeout

    @property
    def verify_cert(self):
        return self.http_client.verify

    @property
    def cert(self):
        return self.http_client.cert

    @property
    def region_name(self):
        return self.http_client.region_name

    @property
    def auth_domain_id(self):
        return self.auth_ref.domain_id

    @property
    def auth_tenant_id(self):
        return self.auth_ref.tenant_id

    @property
    def auth_user_id(self):
        return self.auth_ref.user_id

    @property
    def auth_ref(self):
        try:
            return self.auth_plugin.access_info
        except AttributeError:
            return None

    @auth_ref.setter
    def auth_ref(self, value):
        self.auth_plugin.access_info = value

    @property
    def auth_token(self):
        if self.auth_token_from_user:
            return self.auth_token_from_user
        if self.auth_ref:
            if self.auth_ref.will_expire_soon(self.stale_duration):
                self.authenticate()
            return self.auth_ref.auth_token

    @auth_token.setter
    def auth_token(self, value):
        self.auth_token_from_user = value

    @auth_token.deleter
    def auth_token(self):
        try:
            del self.auth_plugin.opts["token"]
        except KeyError:
            pass

    @property
    def auth_token_from_user(self):
        return self.auth_plugin.opts.get("token")

    @auth_token_from_user.setter
    def auth_token_from_user(self, value):
        self.auth_plugin.opts["token"] = value

    @property
    def auth_url(self):
        return (self.auth_plugin.opts.get("auth_url") or
                (self.auth_ref and self.auth_ref.auth_url[0]))

    def _get_opts_or_auth_ref(self, name):
        return (self.auth_plugin.opts.get(name) or
                (self.auth_ref and getattr(self.auth_ref, name)))

    @property
    def domain_id(self):
        return self._get_opts_or_auth_ref("domain_id")

    @property
    def domain_name(self):
        return self._get_opts_or_auth_ref("domain_name")

    @property
    def management_url(self):
        return (self.auth_plugin.opts.get("endpoint") or
                (self.auth_ref and self.auth_ref.management_url and
                 self.auth_ref.management_url[0]))

    @management_url.setter
    def management_url(self, value):
        self.auth_plugin.opts["endpoint"] = value

    @property
    def password(self):
        return self.auth_plugin.opts.get("password")

    @property
    def project_domain_id(self):
        return self._get_opts_or_auth_ref("project_domain_id")

    @property
    def project_domain_name(self):
        return self._get_opts_or_auth_ref("project_domain_name")

    @property
    def project_id(self):
        return self._get_opts_or_auth_ref("project_id")

    @project_id.setter
    def project_id(self, value):
        self.auth_plugin.opts["project_id"] = value

    @property
    def project_name(self):
        return self._get_opts_or_auth_ref("project_name")

    @property
    def user_domain_id(self):
        return self._get_opts_or_auth_ref("user_domain_id")

    @property
    def user_domain_name(self):
        return self._get_opts_or_auth_ref("user_domain_name")

    @property
    def user_id(self):
        return self._get_opts_or_auth_ref("user_id")

    @user_id.setter
    def user_id(self, value):
        self.auth_plugin.opts["user_id"] = value

    @property
    def username(self):
        return self._get_opts_or_auth_ref("username")

    @property
    def service_catalog(self):
        """Returns this client's service catalog."""
        return self.auth_ref.service_catalog

    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return self.auth_ref.has_service_catalog()

    @property
    def tenant_id(self):
        """Provide read-only backwards compatibility for tenant_id.
           This is deprecated, use project_id instead.
        """
        return self.project_id

    @property
    def tenant_name(self):
        """Provide read-only backwards compatibility for tenant_name.
           This is deprecated, use project_name instead.
        """
        return self.project_name

    def authenticate(self, **kwargs):
        """Authenticate user.

        Uses the data provided at instantiation to authenticate against
        the Identity server. This may use either a username and password
        or token for authentication. If a tenant name or id was provided
        then the resulting authenticated client will be scoped to that
        tenant and contain a service catalog of available endpoints.

        With the v2.0 API, if a tenant name or ID is not provided, the
        authentication token returned will be 'unscoped' and limited in
        capabilities until a fully-scoped token is acquired.

        With the v3 API, if a domain name or id was provided then the resulting
        authenticated client will be scoped to that domain. If a project name
        or ID is not provided, and the authenticating user has a default
        project configured, the authentication token returned will be 'scoped'
        to the default project. Otherwise, the authentication token returned
        will be 'unscoped' and limited in capabilities until a fully-scoped
        token is acquired.

        If successful, sets the self.auth_ref and self.auth_token with
        the returned token. If not already set, will also set
        self.management_url from the details provided in the token.

        kwargs can include the following options to override them in
        `self.auth_plugin`:
        * username
        * password
        * tenant_name
        * tenant_id
        * auth_url
        * token
        * user_id
        * domain_name
        * domain_id
        * project_name
        * project_id
        * user_domain_id
        * user_domain_name
        * project_domain_id
        * project_domain_name

        :returns: ``True`` if authentication was successful.
        :raises: AuthorizationFailure if unable to authenticate or validate
                 the existing authorization token
        :raises: ValueError if insufficient parameters are used.

        If keyring is used, token is retrieved from keyring instead.
        Authentication will only be necessary if any of the following
        conditions are met:

        * keyring is not used
        * if token is not found in keyring
        * if token retrieved from keyring is expired or about to
          expired (as determined by stale_duration)
        * if force_new_token is true

        """
        self.auth_plugin.opts.update(kwargs)

        auth_ref = getattr(self.auth_plugin, "access_info", None)
        if auth_ref and not (kwargs.get('token') or
                             self.auth_plugin.opts.get('token') or
                             auth_ref.will_expire_soon(self.stale_duration)):
            token = auth_ref.auth_token
            if token:
                self.auth_plugin.opts["token"] = token

        keyring_keys = (
            'auth_url',
            'user_id',
            'username',
            'user_domain_id',
            'user_domain_name',
            'domain_id',
            'domain_name',
            'project_id',
            'project_name',
            'project_domain_id',
            'project_domain_name',
            'token',
        )
        keyring_kwargs = dict(
            (key, self.auth_plugin.opts.get(key, None))
            for key in keyring_keys)
        (keyring_key, auth_ref) = self.get_auth_ref_from_keyring(
            **keyring_kwargs)
        new_token_needed = False
        if auth_ref is None or self.force_new_token:
            new_token_needed = True
            self.http_client.authenticate()
        else:
            self.auth_plugin.access_info = auth_ref
        if new_token_needed:
            self.store_auth_ref_into_keyring(keyring_key)
        return True

    def _build_keyring_key(self, **kwargs):
        """Create a unique key for keyring.

        Used to store and retrieve auth_ref from keyring.

        Returns a slash-separated string of values ordered by key name.

        """
        return '/'.join([kwargs[k] or '?' for k in sorted(kwargs.keys())])

    def get_auth_ref_from_keyring(self, **kwargs):
        """Retrieve auth_ref from keyring.

        If auth_ref is found in keyring, (keyring_key, auth_ref) is returned.
        Otherwise, (keyring_key, None) is returned.

        :returns: (keyring_key, auth_ref) or (keyring_key, None)
        :returns: or (None, None) if use_keyring is not set in the object

        """
        keyring_key = None
        auth_ref = None
        if self.use_keyring:
            keyring_key = self._build_keyring_key(**kwargs)
            try:
                auth_ref = keyring.get_password("keystoneclient_auth",
                                                keyring_key)
                if auth_ref:
                    auth_ref = pickle.loads(auth_ref)
                    if auth_ref.will_expire_soon(self.stale_duration):
                        # token has expired, don't use it
                        auth_ref = None
            except Exception as e:
                auth_ref = None
                _logger.warning('Unable to retrieve token from keyring %s' % (
                    e))
        return (keyring_key, auth_ref)

    def store_auth_ref_into_keyring(self, keyring_key):
        """Store auth_ref into keyring.

        """
        if self.use_keyring:
            try:
                keyring.set_password("keystoneclient_auth",
                                     keyring_key,
                                     pickle.dumps(self.auth_ref))
            except Exception as e:
                _logger.warning("Failed to store token into keyring %s" % (e))

    def process_token(self):
        """Deprecated, kept for compatibility.

        Previous task: extract and process information from the new auth_ref.
        And set the relevant authentication information.
        """
        pass

    def get_raw_token_from_identity_service(self, auth_url, username=None,
                                            password=None, tenant_name=None,
                                            tenant_id=None, token=None,
                                            user_id=None, user_domain_id=None,
                                            user_domain_name=None,
                                            domain_id=None, domain_name=None,
                                            project_id=None, project_name=None,
                                            project_domain_id=None,
                                            project_domain_name=None):
        """Deprecated, kept for compatibility.

        Previous task: authenticate against the Identity API and get a token.

        Not implemented here because auth protocols should be API
        version-specific.

        Expected to authenticate or validate an existing authentication
        reference already associated with the client. Invoking this call
        *always* makes a call to the Identity service.
        """
        pass

    def serialize(self, entity):
        return json.dumps(entity)

    @property
    def service_catalog(self):
        """Returns this client's service catalog."""
        return self.auth_ref.service_catalog

    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return self.auth_ref.has_service_catalog()
