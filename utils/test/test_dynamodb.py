"""Unit tests for dynamodb utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockDynamoDbClient(object):
    """Used to mock dynamodb client"""

    def __init__(self):
        self.paginator = {}
        self.table_names = ["table-1", "table-2"]
        self.region = 'us-east-1'
        self.table_arn = [f"arn:aws:dynamodb:us-east-1:123456789012:table/{table_name}"
                          for table_name in self.table_names]
        self.global_tables_arn = [f"arn:aws:dynamodb::123456789012:global-table/{table_name}"
                                  for table_name in self.table_names]

    def get_arn_list(self):
        return self.table_arn + self.global_tables_arn

    def get_paginator(self, action):
        self.paginator = DynamoDBPaginatorClass(self.table_names, self.region, action)
        return self.paginator

    def list_global_tables(self, **kwargs):
        global_tables_page_iterator = {'GlobalTables': [{'GlobalTableName': table_name,
                                                        'ReplicationGroup': [{'RegionName': self.region}]}
                                                        for table_name in self.table_names]}
        return global_tables_page_iterator

    def describe_table(self, **kwargs):
        return {'Table': {'TableArn': f"arn:aws:dynamodb:us-east-1:123456789012:table/{kwargs.get('TableName')}"}}

    def describe_global_table(self, **kwargs):
        return {'GlobalTableDescription': {'GlobalTableArn':
                                           f"arn:aws:dynamodb::123456789012:global-table/"
                                           f"{kwargs.get('GlobalTableName')}"}}


class DynamoDBPaginatorClass:
    def __init__(self, table_names, region, action):
        self.table_names = table_names
        self.region = region
        self.action = action

    def paginate(self):
        list_tables_page_iterator = [{'TableNames': [table_name]} for table_name in self.table_names]
        if self.action == 'list_tables':
            return list_tables_page_iterator


class TestDynamodb(TestCase):

    def test_get_dynamodb_tables(self):
        """Test the method to get all the dynamodb table arns in a given region"""
        from utils.dynamodb import get_dynamodb_tables
        dynamodb_client = MockDynamoDbClient()
        dynamodb_arn_list = get_dynamodb_tables(dynamodb_client, "us-east-1")
        self.assertEqual(dynamodb_arn_list, dynamodb_client.get_arn_list())


if __name__ == '__main__':
    unittest.main()
