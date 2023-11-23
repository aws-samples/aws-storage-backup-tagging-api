"""Unit tests for resource groups tagging api utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockResourceGroupsTaggingApiClient(object):
    """Used to mock ResourceGroupsTaggingAPI Client"""

    def __init__(self):
        self.paginator = {}
        self.resource_arns = [
            "arn:aws:redshift:us-east-1:594917905844:namespace:e7089e44-2310-4952-9bc2-c88bddf9bd26",
            "arn:aws:rds:us-east-1:123456789012:ri:reserved_db_instance_name",
        ]

    def get_paginator(self, action):
        self.paginator = ResourceGroupsTaggingApiPaginatorClass(self.resource_arns, action)
        return self.paginator

    @staticmethod
    def tag_resources(**kwargs):
        return None

    @staticmethod
    def untag_resources(**kwargs):
        return None

    def get_arn_list(self):
        return self.resource_arns


class ResourceGroupsTaggingApiPaginatorClass:
    def __init__(self, resource_arns, action):
        self.action = action
        self.resource_arns = resource_arns

    def paginate(self, **kwargs):
        return [{'ResourceTagMappingList': [{'ResourceARN': arn} for arn in self.resource_arns]}]


class TestResourceGroupsTaggingApi(TestCase):

    def test_get_all_resources_to_skip(self):
        """Test the method to get all the resources that have the skip backup tag"""
        from utils.resource_groups_tagging_api import get_all_resources_to_skip
        resource_groups_tagging_api_client = MockResourceGroupsTaggingApiClient()
        resources_to_skip_arn_list = get_all_resources_to_skip(resource_groups_tagging_api_client)
        self.assertEqual(resources_to_skip_arn_list, resource_groups_tagging_api_client.get_arn_list())

    def test_tag_storage_resources_to_skip(self):
        """Test the method to tag all the given arns in a given region"""
        from utils.resource_groups_tagging_api import tag_storage_resources
        resource_groups_tagging_api_client = MockResourceGroupsTaggingApiClient()
        arns_to_skip = ["arn:aws:rds:us-east-1:123456789012:ri:reserved_db_instance_name"]
        tag_list = {
            "test_key": "test_value"
        }
        tag_storage_resources(resource_groups_tagging_api_client, tag_list, arns_to_skip)

    def test_untag_storage_resources_to_skip(self):
        """Test the method to untag all the given arns in a given region"""
        from utils.resource_groups_tagging_api import untag_storage_resources_to_skip
        resource_groups_tagging_api_client = MockResourceGroupsTaggingApiClient()
        arns_to_skip = ["arn:aws:rds:us-east-1:123456789012:ri:reserved_db_instance_name"]
        untag_storage_resources_to_skip(resource_groups_tagging_api_client, arns_to_skip, ['vpcx-backup'])


if __name__ == '__main__':
    unittest.main()
