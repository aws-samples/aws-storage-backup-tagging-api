"""
contains behave step implementation
"""
# pylint: disable = import-error,no-name-in-module,line-too-long,C0111,W0603,W0613

import json

import botocore.exceptions
import requests
from hamcrest import assert_that, equal_to, has_item, contains_string, not_
import os
import sys
from behave import then, given, when

THISDIR = os.path.dirname(__file__)  # steps/
TESTSDIR = os.path.dirname(THISDIR)  # bdd/

sys.path.insert(0, TESTSDIR)
sys.path.insert(0, THISDIR)

from tests import config, logger
from utils.bdd_utils import boto3_client


@given(u'the api /v1/accounts/<account>/regions/<region>/exceptions/backup/enable exists')
@given(u'the api /v1/accounts/<account>/regions/<region>/exceptions/backup/<enable/disable> exists')
def step_impl(context):
    """
    Build the url with config items
    """
    account = config['main']['account']
    region = config['main']['region']
    vpce = config['behave']['vpc_endpoint']
    env = config['main']['environment']

    context.url = f'https://{vpce}/{env}/v1/accounts/{account}/regions/{region}/exceptions/backup/enable'
    print(context.url)
    logger.info('--------------------------')
    logger.info(context.url)
    logger.info('--------------------------')


@given(u'the api /v1/accounts/<account>/regions/<region>/exceptions/backup/disable exists')
def step_impl(context):
    """
    Build the url with config items
    """
    account = config['main']['account']
    region = config['main']['region']
    vpce = config['behave']['vpc_endpoint']
    env = config['main']['environment']

    context.url = f'https://{vpce}/{env}/v1/accounts/{account}/regions/{region}/exceptions/backup/disable'
    print(context.url)
    logger.info('--------------------------')
    logger.info(context.url)
    logger.info('--------------------------')


@given(u'the auth token is valid')
def step_imp(context):
    """
    Get a valid token for the put storage tags API
    """
    logger.info("Getting auth token...")
    context.token = context.api_client.get_access_token(context.application_scope)


@given(u'the auth token is invalid')
def step_impl(context):
    """
    Set an invalid access token
    """
    logger.info("Setting the invalid auth token...")
    context.token = "invalid_token"


@given(u'the account is valid')
def step_imp(context):
    """
    Set the valid account from the config
    """
    account = config['main']['account']
    context.account = account


@given(u'the account is invalid')
def step_impl(context):
    """
    Set an invalid account in the API url.
    """
    account = 'invalid_account'
    region = config['main']['region']
    vpce = config['behave']['vpc_endpoint']
    env = config['main']['environment']

    context.url = f'https://{vpce}/{env}/v1/accounts/{account}/regions/{region}/resourceType/storage'
    print(context.url)
    logger.info('--------------------------')
    logger.info(context.url)
    logger.info('--------------------------')


@given(u'the region is valid')
def step_impl(context):
    """
    Set the valid region from the config
    """
    region = config['main']['region']
    context.region = region


@given(u'the region is invalid')
def step_impl(context):
    """
    Mark the region invalid in the API url.
    """
    account = config['main']['account']
    region = "invalid_region"
    vpce = config['behave']['vpc_endpoint']
    env = config['main']['environment']

    context.url = f'https://{vpce}/{env}/v1/accounts/{account}/regions/{region}/resourceType/storage'
    print(context.url)
    logger.info('--------------------------')
    logger.info(context.url)
    logger.info('--------------------------')


@given(u'the request body contains valid resource list')
def step_impl(context):
    """
    Set valid tag keys in the request body
    :param context:
    :return:
    """
    context.request_body = context.exception_request_body


@given(u'the request body contains invalid resource list')
def step_impl(context):
    """Prepare an invalid resource list"""
    context.request_body = {
        'resource_arns': ["invalid_resource_arn"],
        'volume_ids': ["invalid_volume_id"]
    }


@when(u'we invoke the api')
def step_impl(context):
    """
    Invoke the put storage tags API
    """
    logger.info("Invoking API")
    headers = {
        'authorization': context.token,
        'Host': context.api_host
    }
    kwargs = {
        'headers': headers
    }
    method = 'PUT'
    logger.info("---------------------------------")
    logger.info("Making API call")
    logger.info("---------------------------------")
    response = requests.request(method, context.url, **kwargs, json=context.request_body)
    logger.info("---------------------------------")
    logger.info("Response: %s", response)
    logger.info("Response details: %s", response.text)
    logger.info("Response headers: %s", response.headers)
    logger.info("Response url: %s", response.url)

    context.status_code = response.status_code
    context.response_data = (json.loads(response.text))


@then(u'response code of 200 is returned')
def step_impl(context):
    """
    Assert that the API response code is 200
    :param context:
    :return:
    """
    assert_that(context.status_code, equal_to(200))


@then(u'response code of 400 is returned')
def step_impl(context):
    """
    Assert that the API response code is 400
    :param context:
    :return:
    """
    assert_that(context.status_code, equal_to(400))


@then(u'response code of 401 is returned')
def step_impl(context):
    """
    Assert that the API response code is 401
    :param context:
    :return:
    """
    assert_that(context.status_code, equal_to(401))


@then(u'response code of 404 is returned')
def step_impl(context):
    """
    Assert that the API response code is 404
    :param context:
    :return:
    """
    assert_that(context.status_code, equal_to(404))


@then(u'all the storage resources in the request body are tagged with the tag key `vpcx-skip-backup` and tag value `true`')
def step_impl(context):
    """
    Check the tags on all the resources
    """
    # Refresh the credentials as the resources creation time might have caused the credentials to expire.
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.resource_tagging_client = boto3_client(test_creds, 'resourcegroupstaggingapi', context.region)

    paginator = context.resource_tagging_client.get_paginator('get_resources')
    response_iterator = paginator.paginate(
        ResourceARNList=context.bdd_resource_arn_list
    )
    logger.info(f"Resources being checked: {context.bdd_resource_arn_list}")
    expected_tags = []
    ebs_volumes_expected_tags = []
    for key in context.enable_bdd_tag_list:
        expected_tags.append({
            'Key': key,
            'Value': context.enable_bdd_tag_list.get(key)
        })
    for page in response_iterator:
        for resource in page.get('ResourceTagMappingList'):
            for tag in expected_tags:
                assert_that(resource.get('Tags'), has_item(tag))

    # Check all the EBS volumes as they aren't tagged using ARNs
    for volume_id in context.ebs_volumes_ids:
        for key in context.enable_bdd_tag_list:
            ebs_volumes_expected_tags.append({
                'Key': key,
                'ResourceId': volume_id,
                'ResourceType': 'volume',
                'Value': context.enable_bdd_tag_list.get(key)
            })
    response = context.ec2_client.describe_tags(
        Filters=[{
            'Name': 'resource-id',
            'Values': context.ebs_volumes_ids
        }]
    )
    for tag in ebs_volumes_expected_tags:
        assert_that(response.get('Tags'), has_item(tag))


@then(u'the message is \'storage resources tagged \
        with tag key vpcx-skip-backup and tag value false\'')
def step_impl(context):
    """Assert the message returned by the API
    """
    assert_that(
        context.response_data,
        equal_to(
            {
                'message': 'storage resources tagged with tag key vpcx-skip-backup and tag value false'
            }
        )
    )


@then(u'the message is \'storage resources tagged with tag key vpcx-skip-backup and tag value true\'')
def step_impl(context):
    """Assert the message returned by the API
    """
    assert_that(
        context.response_data,
        equal_to(
            {
                'message': 'storage resources tagged with tag key vpcx-skip-backup and tag value true'
            }
        )
    )


@then(u'the error message is \'unauthorized\'')
def step_impl(context):
    """Assert the unauthorized response by the API"""
    assert_that(context.response_data.get('error'), contains_string('Unauthorized'))


@then(u'the error message is \'region not found\'')
def step_impl(context):
    """Assert the API response when region is invalid"""
    assert_that(context.response_data, equal_to({'error': 'Please enter a valid region in the url path'}))


@then(u'the error message is \'account not found\'')
def step_impl(context):
    """Assert the API response when region is invalid"""
    assert_that(context.response_data, equal_to({'error': 'ValueError: Invalid account: {self.__project_id}'}))


@then(u'error message is \'One of the resources in the request is invalid.\'')
def step_impl(context):
    """Assert that the invalid resource arns are returned by the API"""
    assert_that(context.response_data.get('error'),
                contains_string('One of the resources in the request is invalid. Details :'))


@then(u'all the storage resources in the request body are un tagged with the tag key `vpcx-skip-backup`')
def step_impl(context):
    """Check all the resources have been un tagged with tag key vpcx-skip-backup"""
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.resource_tagging_client = boto3_client(test_creds, 'resourcegroupstaggingapi', context.region)

    paginator = context.resource_tagging_client.get_paginator('get_resources')
    response_iterator = paginator.paginate(
        ResourceARNList=context.bdd_resource_arn_list
    )
    logger.info(f"Resources being checked: {context.bdd_resource_arn_list}")
    expected_tags = []
    ebs_volumes_expected_tags = []
    for key in context.enable_bdd_tag_list:
        expected_tags.append({
            'Key': key,
            'Value': context.enable_bdd_tag_list.get(key)
        })
    for page in response_iterator:
        for resource in page.get('ResourceTagMappingList'):
            for tag in expected_tags:
                assert_that(resource.get('Tags'), not_(has_item(tag)))

    # Check all the EBS volumes as they aren't tagged using ARNs
    for volume_id in context.ebs_volumes_ids:
        for key in context.enable_bdd_tag_list:
            ebs_volumes_expected_tags.append({
                'Key': key,
                'ResourceId': volume_id,
                'ResourceType': 'volume',
                'Value': context.enable_bdd_tag_list.get(key)
            })
    response = context.ec2_client.describe_tags(
        Filters=[{
            'Name': 'resource-id',
            'Values': context.ebs_volumes_ids
        }]
    )
    for tag in ebs_volumes_expected_tags:
        assert_that(response.get('Tags'), not_(has_item(tag)))


@then(u'the message is \'storage resources un tagged with tag key vpcx-skip-backup\'')
def step_impl(context):
    """Assert that the skip disablement is successful"""
    assert_that(
        context.response_data,
        equal_to(
            {
                'message': 'storage resources un tagged with tag key vpcx-skip-backup'
            }
        )
    )
