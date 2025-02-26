import modules.dns_utils as dns_utils
import modules.one_com_config as config
import modules.one_com_api as one_com_api
import logging
import requests
import unittest
from unittest.mock import patch, Mock
import json
import sys  # Make sure sys is imported

# Setup basic logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class TestOneComDDNS(unittest.TestCase):

    def test_dns_utils_get_ip_and_ttl(self):
        ip, ttl = dns_utils.get_ip_and_ttl("google.com")
        self.assertIsNotNone(ip)
        self.assertIsNotNone(ttl)
        self.assertIsInstance(ip, str)
        self.assertIsInstance(ttl, int)

        result_invalid = dns_utils.get_ip_and_ttl("invalid-domain-for-testing.com")
        self.assertIsNone(result_invalid)

    def test_one_com_config_parse_config(self):
        with patch('sys.argv', ['test_script.py', '-u', 'testuser', '-p', 'testpass', '-d', 'test.com', '-i', '127.0.0.1', '-f', '-t', '300', '-y']):
            settings = config.parse_config(validate_required=True)
            self.assertEqual(settings.username, 'testuser')
            self.assertEqual(settings.password, 'testpass')
            self.assertEqual(settings.domains, ['test.com'])
            self.assertEqual(settings.ip, '127.0.0.1')
            self.assertTrue(settings.force_update)
            self.assertEqual(settings.ttl, 300)
            self.assertTrue(settings.skip_confirmation)

    def test_one_com_config_parse_config_auto_ip(self):
        with patch('sys.argv', ['test_script.py', '-u', 'testuser', '-p', 'testpass', '-d', 'test.com', '-i', 'AUTO']):
            with patch('requests.get') as mock_get:
                mock_get.return_value.text = "1.2.3.4"
                settings = config.parse_config(validate_required=True)
                self.assertEqual(settings.ip, "1.2.3.4")

    def test_one_com_config_parse_config_auto_ip_error(self):
        with patch('sys.argv', ['test_script.py', '-u', 'testuser', '-p', 'testpass', '-d', 'test.com', '-i', 'AUTO']):
            with patch('requests.get') as mock_get:
                mock_get.side_effect = requests.ConnectionError
                with self.assertRaises(SystemExit):
                    config.parse_config(validate_required=True)

    def test_one_com_api_login_session(self):
        with patch('requests.sessions.Session.get') as mock_get:
            mock_get.return_value.text = '<form id="kc-form-login" class="Login-form login autofill" onsubmit="login.disabled = true; return true;" action="test_url"></form>'
            with patch('requests.sessions.Session.post') as mock_post:
                mock_post.return_value.text = "Success"
                session = one_com_api.login_session("testuser", "testpass")
                self.assertIsNotNone(session)
        with patch('requests.sessions.Session.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError
            with self.assertRaises(SystemExit):
                one_com_api.login_session("testuser", "testpass")

    def test_one_com_api_get_custom_records(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"result": {"data": [{"id": "123", "attributes": {"prefix": "test"}} ]}}'
        mock_session.get.return_value = mock_response

        records = one_com_api.get_custom_records(mock_session, "test.com")
        self.assertIsNotNone(records)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], "123")

        mock_session.get.side_effect = requests.exceptions.RequestException("Test Exception")
        raised_system_exit = False
        try:
            one_com_api.get_custom_records(mock_session, "test.com")
        except SystemExit:
            raised_system_exit = True
        self.assertTrue(raised_system_exit, "SystemExit was not raised")

        mock_session.get.side_effect = None
        mock_response.text = '{"result": {"data": "invalid json"}}'
        mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_session.get.return_value = mock_response
        with self.assertRaises(SystemExit):
            one_com_api.get_custom_records(mock_session, "test.com")

    def test_one_com_api_find_id_by_subdomain(self):
        records = [{"id": "1", "attributes": {"prefix": "sub"}}, {"id": "2", "attributes": {"prefix": "other"}}]
        record_obj = one_com_api.find_id_by_subdomain(records, "sub.test.com")
        self.assertEqual(record_obj['id'], "1")

        record_obj_not_found = one_com_api.find_id_by_subdomain(records, "nonexistent.test.com")
        self.assertIsNone(record_obj_not_found)

    def test_one_com_api_change_ip(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.patch.return_value = mock_response

        record = {"id": "123", "attributes": {"ttl": 300}}
        one_com_api.change_ip(mock_session, record, "sub.test.com", "1.2.3.4", 600)

        mock_session.patch.side_effect = requests.exceptions.RequestException("Test Exception")
        with self.assertRaises(SystemExit):
            one_com_api.change_ip(mock_session, record, "sub.test.com", "1.2.3.4", 600)

    def test_dns_utils_get_authoritative_ns(self):
        ns_servers = dns_utils.get_authoritative_ns("google.com")
        self.assertIsNotNone(ns_servers)
        self.assertIsInstance(ns_servers, list)
        self.assertGreater(len(ns_servers), 0)

        ns_servers_invalid = dns_utils.get_authoritative_ns("invalid-domain-for-testing.com")
        self.assertIsNone(ns_servers_invalid)

    def test_dns_utils_get_authoritative_ns_parent(self):
        ns_servers = dns_utils.get_authoritative_ns("sub.google.com")
        self.assertIsNotNone(ns_servers)
        self.assertIsInstance(ns_servers, list)
        self.assertGreater(len(ns_servers), 0)

if __name__ == '__main__':
    unittest.main()