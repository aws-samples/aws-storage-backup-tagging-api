"""Unit tests for secrets manager api utils"""
import os
from unittest import TestCase
import unittest
import json

# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockSecretsManagerClient(object):
    """Used to mock ResourceGroupsTaggingAPI Client"""

    def __init__(self):
        self.secret_response = {
            'SecretString': json.dumps({'PASSWORD': 'test_secret_value'})
        }

    def get_secret_value(self, **kwargs):
        return self.secret_response

    def get_secret_response_value(self):
        return json.loads(self.secret_response['SecretString'])['PASSWORD']


class TestResourceGroupsTaggingApi(TestCase):

    def test_retrieve_ldap_password(self):
        """Test the method to get the ldap password from secrets manager"""
        from utils.secrets import retrieve_ldap_password
        import logging
        secrets_manager_client = MockSecretsManagerClient()
        secret_value = retrieve_ldap_password(secrets_manager_client, logging.getLogger(), "test_secret_name")
        self.assertEqual(secret_value, secrets_manager_client.get_secret_response_value())


if __name__ == '__main__':
    unittest.main()
