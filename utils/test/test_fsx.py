"""Unit tests for fsx utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockFSXClient(object):
    """Used to mock FSX Client"""

    def __init__(self):
        self.paginator = {}
        self.file_system_ids = ['fs-004daba0130280f75',
                                'fs-004daba0130280f76',
                                'fs-004daba0130280f77',
                                'fs-004daba0130280f78',
                                'fs-004daba0130280f79']
        self.file_system_arns = [f"arn:aws:fsx:us-east-1:123456789012:file-system/{file_system_id}"
                                 for file_system_id in self.file_system_ids]

    def get_paginator(self, action):
        self.paginator = FSXPaginatorClass(self.file_system_ids, action)
        return self.paginator

    def get_arn_list(self):
        return self.file_system_arns


class FSXPaginatorClass:
    def __init__(self, file_system_ids, action):
        self.action = action
        self.file_system_ids = file_system_ids

    def paginate(self, **kwargs):
        return [{'FileSystems': [{'ResourceARN':
                                  f"arn:aws:fsx:us-east-1:123456789012:file-system/{file_system_id}"}
                                 for file_system_id in self.file_system_ids]}]


class TestFSX(TestCase):

    def test_get_fsx_file_systems(self):
        """Test the method to get all the fsx file system arns in a given region"""
        from utils.fsx import get_fsx_file_systems
        fsx_client = MockFSXClient()
        fsx_arn_list = get_fsx_file_systems(fsx_client)
        self.assertEqual(fsx_arn_list, fsx_client.get_arn_list())


if __name__ == '__main__':
    unittest.main()
