"""Unit tests for ebs utils"""
import os
from unittest import TestCase
import unittest
# pylint: disable = no-name-in-module,import-error,no-self-use,broad-except, C0413, C0411, C0330

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class MockEC2Client(object):
    """Used to mock EBS Client"""

    def __init__(self):
        self.paginator = {}
        self.volume_ids = ['vol-012ea34a439822303',
                           'vol-01241dfaef14f8780',
                           'vol-0e01b20eb1dcbabdf',
                           'vol-09a8686792f3aae5f',
                           'vol-000dee67be941d7e2']

    def get_paginator(self, action):
        self.paginator = EBSPaginatorClass(self.volume_ids, action)
        return self.paginator

    @staticmethod
    def create_tags(**kwargs):
        return None


class EBSPaginatorClass:
    def __init__(self, volume_ids, action):
        self.action = action
        self.volume_ids = volume_ids

    def paginate(self, **kwargs):
        if kwargs.get('Filters'):
            if kwargs.get('Filters') == [{'Name': 'tag:vpcx-skip-backup', 'Values': ['true']}]:
                return [{'Volumes': [{'VolumeId': self.volume_ids[0]}]}]
        return [{'Volumes': [{'VolumeId': volume_id} for volume_id in self.volume_ids]}]


class TestEBS(TestCase):

    def test_tag_all_ebs_volumes(self):
        """Test the method to tag all the ebs volumes in a given region"""
        from utils.ebs import tag_all_ebs_volumes
        ec2_client = MockEC2Client()
        tag_all_ebs_volumes(ec2_client, {'dummy-key': 'dummy-value'}, {'vpcx-backup': 'regular'})


if __name__ == '__main__':
    unittest.main()
