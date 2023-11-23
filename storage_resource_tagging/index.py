"""
This module contains the lambda function code for put-storage-tags API.

This file uses environment variables in place of config; thus
sddcapi_boot_dir is not required.
"""

# pylint: disable=import-error,logging-format-interpolation,broad-except,too-many-statements,C0413,W1203,R1703,R0914
import boto3
import botocore.exceptions
import os
import sys
import json
import logging
import traceback
#from cloudx_sls_authorization import lambda_auth

THISDIR = os.path.dirname(__file__)  # storage_resource_tagging
APPDIR = os.path.dirname(THISDIR)  # resource_tagging

if APPDIR not in sys.path:
    sys.path.append(APPDIR)
if THISDIR not in sys.path:
    sys.path.append(THISDIR)

from utils import api_request
from utils import dynamodb, ebs, efs, fsx, rds, redshift, resource_groups_tagging_api, helpers, secrets
from utils.exceptions import InvalidRegionException, InvalidInputException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define LDAP lookup configs
LDAP_SERVER = os.environ['LDAP_SERVER']
LDAP_USERNAME = os.environ['LDAP_USERNAME']
LDAP_PASSWORD_SECRET_NAME = os.environ['LDAP_PASSWORD_SECRET_NAME']
LDAP_SEARCH_BASE = os.environ['LDAP_SEARCH_BASE']
LDAP_OBJECT_CLASS = os.environ['LDAP_OBJECT_CLASS']
LDAP_GROUP_NAME = os.environ['LDAP_GROUP_NAME'].split(',')
LDAP_LOOKUP_ATTRIBUTE = os.environ['LDAP_LOOKUP_ATTRIBUTE']
MSFT_IDP_TENANT_ID = os.environ['MSFT_IDP_TENANT_ID']
MSFT_IDP_APP_ID = os.environ['MSFT_IDP_APP_ID'].split(',')
MSFT_IDP_CLIENT_ROLES = os.environ['MSFT_IDP_CLIENT_ROLES'].split(',')


def handler(event, context):
    """
    Handles an API
    Args:
        event (dict): Lambda Event object prepared by API Gateway
        {
            "resource": "Resource path",
            "path": "Path parameter",
            "httpMethod": "Incoming request's method name"
            "headers": {String containing incoming request headers}
            "multiValueHeaders": {List of strings containing incoming request headers}
            "queryStringParameters": {query string parameters }
            "multiValueQueryStringParameters": {List of query string parameters}
            "pathParameters":  {path parameters}
            "stageVariables": {Applicable stage variables}
            "requestContext": {Request context, including authorizer-returned key-value pairs}
            "body": "A JSON string of the request payload."
            "isBase64Encoded": "A boolean flag to indicate if the applicable request payload is Base64-encode"
        }
        context (dict):
            See aws lambda documents. Not used here.
    Returns:
         dict: Defined by API Gateway
        {
            "isBase64Encoded": true|false,
            "statusCode": httpStatusCode,
            "headers": { "headerName": "headerValue", ... },
            "multiValueHeaders": { "headerName": ["headerValue", "headerValue2", ...], ... },
            "body": "..."
        }    """
    logger.info(f'event: {event}\n context: {context}')
    resp = {}
    status_code = 200

    # Validate the input
    tag_list = json.loads(event.get('body', {}))
    vpcx_backup_tag = {}
    valid_vpcx_backup_tag_values = ["regular"]
    if "vpcx-backup" in tag_list:
        vpcx_backup_tag["vpcx-backup"] = tag_list.get("vpcx-backup")
        del tag_list["vpcx-backup"]

    try:
        if len(tag_list.keys()) == 0 and len(vpcx_backup_tag.keys()) == 0:
            # Empty JSON in request body.
            raise InvalidInputException("No tag key-values present in the request body.")

        invalid_tag_value_tag_keys = []
        for key in tag_list.keys():
            if tag_list.get(key) == "":
                invalid_tag_value_tag_keys.append(key)

        if len(invalid_tag_value_tag_keys) > 0:
            # There is at least one tag key with an invalid value
            # Invalid values are any one of the following:
            # [empty_string]
            raise InvalidInputException(f"The request body has empty values for the these "
                                        f"tagKeys: {invalid_tag_value_tag_keys}."
                                        f"Tag values should be non-empty")

        if vpcx_backup_tag:
            if vpcx_backup_tag["vpcx-backup"] not in valid_vpcx_backup_tag_values:
                raise InvalidInputException("Allowed values for the vpcx-backup tag are: [regular]")
    except InvalidInputException as err:
        status_code = 400
        resp = {
            'error': str(err)
        }

    try:
        # Define service client
        secrets_client = boto3.client('secretsmanager')
        # lambda_auth.authorize_lambda_request(event, MSFT_IDP_TENANT_ID, MSFT_IDP_APP_ID,
        #                                      MSFT_IDP_CLIENT_ROLES, LDAP_SERVER, LDAP_USERNAME,
        #                                      secrets.retrieve_ldap_password(secrets_client,
        #                                                                     logger,
        #                                                                     LDAP_PASSWORD_SECRET_NAME
        #                                                                     ),
        #                                      LDAP_SEARCH_BASE,
        #                                      LDAP_OBJECT_CLASS, LDAP_GROUP_NAME, LDAP_LOOKUP_ATTRIBUTE)
        pass
    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 401,
            'body': json.dumps(str(e))
        }

    # Get environment variables
    resp_headers = {
        'Content-Type': 'application/json'
    }
    if hasattr(context, 'local_test'):
        logger.info('Running at local')
    path_params = event.get('pathParameters', {})
    request_headers = event.get('headers', {})
    vpcxiam_endpoint = os.environ.get('vpcxiam_endpoint')
    vpcxiam_scope = os.environ.get('vpcxiam_scope')
    vpcxiam_host = os.environ.get('vpcxiam_host')

    try:
        account = path_params.get('account-id')
        region = path_params.get('region-name')
        resource_type = path_params.get('resource-type')
        logger.info(f"Account to tag resources in: {account}")
        logger.info(f"Region to tag resources in : {region}")
        logger.info(f"Resource_type to tag resources for: {resource_type}")

        # Validate resource type.
        if resource_type != 'storage':
            raise InvalidInputException("resource type should be storage")

        # is authorized?
        logger.info(f'is_authorized({request_headers}, {MSFT_IDP_APP_ID}, '
                    f'{MSFT_IDP_TENANT_ID}, {MSFT_IDP_CLIENT_ROLES}')

        if len(tag_list.keys()) == 0 and len(vpcx_backup_tag.keys()) == 0:
            # Empty JSON in request body.
            raise InvalidInputException("No tag key-values present in the request body.")

        invalid_tag_value_tag_keys = []
        for key in tag_list.keys():
            if tag_list.get(key) == "":
                invalid_tag_value_tag_keys.append(key)

        if len(invalid_tag_value_tag_keys) > 0:
            # There is at least one tag key with an invalid value
            # Invalid values are any one of the following:
            # [empty_string]
            raise InvalidInputException(f"The request body has empty values for the these "
                                        f"tagKeys: {invalid_tag_value_tag_keys}."
                                        f"Tag values should be non-empty")

        # Get the credentials for the account resources will be created in.
        url = (vpcxiam_endpoint +
               f"/v1/accounts/{account}/roles/admin/credentials")
        scope = vpcxiam_scope
        additional_headers = {
            'Host': vpcxiam_host
        }
        api_requests = api_request.ApiRequests()
        credentials = json.loads(
            (api_requests.request(url=url, method='get', scope=scope, additional_headers=additional_headers)).text
        )
        error = credentials.get('error', {})
        if error:
            logger.error(error)
            raise ValueError(error)
        credentials = credentials.get('credentials', {})

        # Validate region.
        ec2_client = boto3.client(
            service_name='ec2',
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        helpers.is_region_valid(ec2_client, region)
        logger.info(f"{region} is a valid region")

        # Region is valid. Create clients for the given region and given account.
        sts_client = boto3.client(
            service_name='sts',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        iam_client = boto3.client(
            service_name='iam',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        ec2_client = boto3.client(
            service_name='ec2',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        rds_client = boto3.client(
            service_name='rds',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        redshift_client = boto3.client(
            service_name='redshift',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        efs_client = boto3.client(
            service_name='efs',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        fsx_client = boto3.client(
            service_name='fsx',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        dynamodb_client = boto3.client(
            service_name='dynamodb',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))
        resource_tagging_client = boto3.client(
            service_name='resourcegroupstaggingapi',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))

        # Get the role name that has been assumed
        role_arn, account_id = helpers.get_caller_role(sts_client, iam_client)

        logger.info(f"Role name: {role_arn}\t Account Number : {account_id}")

        # Get all the storage resources in the account.
        rds_arns = rds.get_rds_instances(rds_client)
        dynamodb_arns = dynamodb.get_dynamodb_tables(dynamodb_client, region)
        efs_arns = efs.get_efs_file_systems(efs_client)
        fsx_arns = fsx.get_fsx_file_systems(fsx_client)
        redshift_arns = redshift.get_redshift_cluster_arns(redshift_client, region, account_id)

        storage_resources_arn_list = rds_arns + dynamodb_arns + efs_arns + fsx_arns + redshift_arns
        logger.info(f"All storage resources in the account: {storage_resources_arn_list}")

        # Skip the resources with the vpcx-skip-backup tag
        # Get all the storage resources in the account that have the tag to skip the vpcx-backups.
        resources_to_skip_arn_list = resource_groups_tagging_api.get_all_resources_to_skip(resource_tagging_client)
        logger.info(f"Resources with skip tag: {resources_to_skip_arn_list}")

        # Filter the ARN list and prepare a list of ARNs that will be tagged with tag list in the request.
        arn_list_to_add_vpcx_tag = helpers.filter_resource_arns(storage_resources_arn_list,
                                                                resources_to_skip_arn_list)
        logger.info(f"Resources to tag vpcx backup tag: {arn_list_to_add_vpcx_tag}")

        logger.info(f"Tag list: {tag_list}")
        logger.info(f"vpcx-backup-tag dict: {vpcx_backup_tag}")

        # Tag all the resources with the tag list in the request.
        if tag_list:
            resource_groups_tagging_api.tag_storage_resources(resource_tagging_client,
                                                              tag_list,
                                                              storage_resources_arn_list)

        if vpcx_backup_tag:
            resource_groups_tagging_api.tag_storage_resources(resource_tagging_client,
                                                              vpcx_backup_tag,
                                                              arn_list_to_add_vpcx_tag)

        # Tag the EBS volumes using the EC2 API.
        ebs.tag_all_ebs_volumes(ec2_client, tag_list, vpcx_backup_tag)

        # Set the response.
        resp = {
            'message': 'All the storage resources have been tagged with the tag list. '
                       'Resources marked to skip vpcx-backups are untagged.'
        }
    # boto3 error;
    except botocore.exceptions.ClientError as err:
        status_code = 500
        resp = {
            'error': f'{type(err).__name__}: {err}'
        }
    except InvalidRegionException:
        status_code = 400
        resp = {
            'error': 'Please enter a valid region in the url path'
        }
    except InvalidInputException as err:
        status_code = 400
        resp = {
            'error': str(err)
        }
    except ValueError as err:
        status_code = 404
        resp = {
            'error': str(err)
        }
    except Exception as err:
        status_code = 500
        resp = {
            'error': f'{type(err).__name__}: {err}'
        }
    resp = helpers.lambda_returns(status_code, resp_headers, json.dumps(resp))
    logger.info(f'response: {resp}')
    return resp
