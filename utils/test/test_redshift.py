"""Unit tests for redshift utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockRedshiftClient(object):
    """Used to mock Redshift Client"""

    def __init__(self):
        self.paginator = {}
        self.region = "us-east-1"
        self.account_id = "123456789012"
        self.redshift_cluster_identifiers = [
            'redshift_cluster_1',
            'redshift_cluster_2',
            'redshift_cluster_3',
            'redshift_cluster_4',
            'redshift_cluster_5',
            ]
        self.redshift_arns = [f"arn:aws:redshift:{self.region}:{self.account_id}:cluster:{cluster_identifier}"
                              for cluster_identifier in self.redshift_cluster_identifiers]

    def get_paginator(self, action):
        self.paginator = RedshiftPaginatorClass(self.redshift_cluster_identifiers, action)
        return self.paginator

    def get_arn_list(self):
        return self.redshift_arns


class RedshiftPaginatorClass:
    def __init__(self, redshift_cluster_identifiers, action):
        self.action = action
        self.redshift_cluster_identifiers = redshift_cluster_identifiers

    def paginate(self, **kwargs):
        return [{'Clusters': [{'ClusterIdentifier':
                               f"{cluster_identifier}"}
                              for cluster_identifier in self.redshift_cluster_identifiers]}]


class TestRedshift(TestCase):

    def test_get_redshift_cluster_arns(self):
        """Test the method to get all the redshift cluster arns in a given region"""
        from utils.redshift import get_redshift_cluster_arns
        redshift_client = MockRedshiftClient()
        redshift_arn_list = get_redshift_cluster_arns(redshift_client,
                                                      redshift_client.region,
                                                      redshift_client.account_id)
        self.assertEqual(redshift_arn_list, redshift_client.get_arn_list())


if __name__ == '__main__':
    unittest.main()
