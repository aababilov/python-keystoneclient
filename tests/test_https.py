import copy
import mock

import requests

from keystoneclient import httpclient
from tests import utils


FAKE_RESPONSE = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
MOCK_REQUEST = mock.Mock(return_value=(FAKE_RESPONSE))


def get_client(token="", endpoint=""):
    cl = httpclient.HTTPClient(
        token=token, endpoint=endpoint,
        cacert="ca.pem", key="key.pem", cert="cert.pem")
    return cl


def get_authed_client():
    return get_client(
        token="token",
        endpoint="https://127.0.0.1:5000")


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        with mock.patch.object(requests.Session, "request", MOCK_REQUEST):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp = cl.get("/hi")
                body = resp.json()
                headers = {"X-Auth-Token": "token",
                           "User-Agent": cl.http_client.user_agent}
                kwargs = copy.copy(self.TEST_REQUEST_BASE)
                kwargs['cert'] = ('cert.pem', 'key.pem')
                kwargs['verify'] = 'ca.pem'
                MOCK_REQUEST.assert_called_with(
                    "GET",
                    "https://127.0.0.1:5000/hi",
                    headers=headers,
                    **kwargs)
                # Automatic JSON parsing
                self.assertEqual(body, {"hi": "there"})

    def test_post(self):
        cl = get_authed_client()

        with mock.patch.object(requests.Session, "request", MOCK_REQUEST):
            cl.post("/hi", json=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.http_client.user_agent
            }
            kwargs = copy.copy(self.TEST_REQUEST_BASE)
            kwargs['cert'] = ('cert.pem', 'key.pem')
            kwargs['verify'] = 'ca.pem'
            MOCK_REQUEST.assert_called_with(
                "POST",
                "https://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **kwargs)

    def test_post_auth(self):
        with mock.patch.object(requests.Session, "request", MOCK_REQUEST):
            cl = httpclient.HTTPClient(
                cacert="ca.pem", key="key.pem",
                cert="cert.pem",
                endpoint="https://127.0.0.1:5000",
                token="token")
            cl.post("/hi", json=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.http_client.user_agent
            }
            kwargs = copy.copy(self.TEST_REQUEST_BASE)
            kwargs['cert'] = ('cert.pem', 'key.pem')
            kwargs['verify'] = 'ca.pem'
            MOCK_REQUEST.assert_called_with(
                "POST",
                "https://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **kwargs)
