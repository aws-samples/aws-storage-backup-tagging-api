"""Unit tests for rds utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockRDSClient(object):
    """Used to mock RDS Client"""

    def __init__(self):
        self.paginator = {}
        self.cluster_names = [
            'rds-cluster-1',
            'rds-cluster-2',
            'rds-cluster-3',
            'rds-cluster-4',
            'rds-cluster-5'
        ]
        self.db_instance_names = [
            'rds_db_instance_1',
            'rds_db_instance_2',
            'rds_db_instance_3',
            'rds_db_instance_4',
            'rds_db_instance_5',
        ]
        self.global_cluster_names = [
            'rds-global-cluster-1',
            'rds-global-cluster-2',
            'rds-global-cluster-3',
            'rds-global-cluster-4',
            'rds-global-cluster-5'
        ]
        self.reserved_db_instance_names = [
            'rds_reserved_db_instance_1',
            'rds_reserved_db_instance_2',
            'rds_reserved_db_instance_3',
            'rds_reserved_db_instance_4',
            'rds_reserved_db_instance_5',
        ]
        self.rds_arn_list = [f"arn:aws:rds:us-east-1:123456789012:db:{instance_name}"
                             for instance_name in self.db_instance_names] + \
                            [f"arn:aws:rds:us-east-1:123456789012:cluster:{cluster_name}"
                             for cluster_name in self.cluster_names] + \
                            [f"arn:aws:rds::123456789012:global-cluster:{cluster_name}"
                             for cluster_name in self.global_cluster_names] + \
                            [f"arn:aws:rds:us-east-1:123456789012:ri:{instance_name}"
                             for instance_name in self.reserved_db_instance_names]

    def get_paginator(self, action):
        self.paginator = RDSPaginatorClass(self.db_instance_names,
                                           self.reserved_db_instance_names,
                                           self.global_cluster_names,
                                           self.cluster_names,
                                           action)
        return self.paginator

    def get_arn_list(self):
        return self.rds_arn_list


class RDSPaginatorClass:
    def __init__(self, db_instance_names, reserved_db_instance_names, global_cluster_names, cluster_names, action):
        self.action = action
        self.db_instance_names = db_instance_names
        self.reserved_db_instance_names = reserved_db_instance_names
        self.global_cluster_names = global_cluster_names
        self.cluster_names = cluster_names

    def paginate(self, **kwargs):
        if self.action == "describe_db_instances":
            return [{'DBInstances': [{'DBInstanceArn':
                                      f"arn:aws:rds:us-east-1:123456789012:db:{instance_name}"}
                                     for instance_name in self.db_instance_names]}]
        elif self.action == "describe_global_clusters":
            return [{'GlobalClusters': [{'GlobalClusterArn':
                                         f"arn:aws:rds::123456789012:global-cluster:{cluster_name}"}
                                        for cluster_name in self.global_cluster_names]}]
        elif self.action == "describe_db_clusters":
            return [{'DBClusters': [{'DBClusterArn':
                                     f"arn:aws:rds:us-east-1:123456789012:cluster:{cluster_name}"}
                                    for cluster_name in self.cluster_names]}]
        elif self.action == "describe_reserved_db_instances":
            return [{'ReservedDBInstances': [{'ReservedDBInstanceArn':
                                              f"arn:aws:rds:us-east-1:123456789012:ri:{instance_name}"}
                                             for instance_name in self.reserved_db_instance_names]}]


class TestRDS(TestCase):

    def test_get_rds_instances(self):
        """Test the method to get all the rds arns in a given region"""
        from utils.rds import get_rds_instances
        rds_client = MockRDSClient()
        rds_arn_list = get_rds_instances(rds_client)
        self.assertEqual(rds_arn_list, rds_client.get_arn_list())


if __name__ == '__main__':
    unittest.main()
