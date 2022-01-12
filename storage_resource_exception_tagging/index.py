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
from utils import ebs, resource_groups_tagging_api, helpers, secrets
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

    resource_list = json.loads(event.get('body', {}))
    volume_ids = resource_list.get('volume_ids', [])
    resource_arn_list = resource_list.get('resource_arns', [])
    valid_exception_actions = ['enable', 'disable']
    tag_list = {}

    if len(volume_ids) == 0 and len(resource_arn_list) == 0:
        raise InvalidInputException("Either resource_arns or volume_ids have to be included in the request body")

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
            'body': json.dumps({'error': f"Unauthorized. {str(e)}"})
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
    resp = {}
    status_code = 200

    try:
        account = path_params.get('account-id')
        region = path_params.get('region-name')
        action = path_params.get('exception-action')
        logger.info(f"Account to tag resources in: {account}")
        logger.info(f"Region to tag resources in : {region}")
        logger.info(f"Action for exception (enable/disable): {action}")

        # Validate exception action.
        if action not in valid_exception_actions:
            raise InvalidInputException("exception-action should be enable or disable")

        # is authorized?
        logger.info(f'is_authorized({request_headers}, {MSFT_IDP_APP_ID}, '
                    f'{MSFT_IDP_TENANT_ID}, {MSFT_IDP_CLIENT_ROLES}')

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
        resource_tagging_client = boto3.client(
            service_name='resourcegroupstaggingapi',
            region_name=region,
            aws_access_key_id=credentials.get('AccessKeyId', ''),
            aws_secret_access_key=credentials.get('SecretAccessKey', ''),
            aws_session_token=credentials.get('SessionToken', ''))

        # Get the role name that has been assumed
        role_arn, account_id = helpers.get_caller_role(sts_client, iam_client)

        logger.info(f"Role name: {role_arn}\t Account Number : {account_id}")

        if action == 'enable':
            tag_list = {
                'vpcx-skip-backup': 'true'
            }

            if len(resource_arn_list) != 0:
                # Tag when the resource arn list is not empty
                # Tag storage resources with vpcx-skip-backup tag
                resource_groups_tagging_api.tag_storage_resources(resource_tagging_client, tag_list, resource_arn_list)

                # Untag storage resource with tag key vpcx-backup and value regular
                resource_groups_tagging_api.untag_storage_resources_to_skip(
                    resource_tagging_client,
                    resource_arn_list,
                    ['vpcx-backup']
                )

            if len(volume_ids) != 0:
                # Tag ebs volumes with vpcx-skip-backup tag.
                # Untag the volumes with tag key vpcx-backup and value regular.
                # Tags with key vpcx-backup and value legal-hold will be kept
                # as is because those resources can't be skipped.
                logger.info(f"Volumes ids that have to be skipped : {volume_ids}")
                ebs.tag_untag_skip_backup_ebs_volumes(ec2_client, volume_ids, tag_list)

        else:
            # The exception action is disable
            if len(resource_arn_list) != 0:
                # Un tag all the resources with the vpcx-skip-backup tag key
                resource_groups_tagging_api.untag_storage_resources_to_skip(
                    resource_tagging_client,
                    resource_arn_list,
                    ['vpcx-skip-backup']
                )

            if len(volume_ids) != 0:
                # Un tag all the volumes with vpcx-skip-backup tag
                for i in range(0, len(volume_ids), 1000):
                    ec2_client.delete_tags(
                        Resources=volume_ids[i:i+1000],
                        Tags=[
                            {
                                'Key': 'vpcx-skip-backup'
                            }
                        ]
                    )

        # Set the response.
        if action == 'enable':
            resp = {
                'message': f"storage resources tagged with tag key vpcx-skip-backup and tag value true"
            }
        else:
            resp = {
                'message': 'storage resources un tagged with tag key vpcx-skip-backup'
            }
    # boto3 error;
    except botocore.exceptions.ClientError as err:
        err_code = err.response['Error']['Code']
        logger.info(f"err_code from boto3: {err_code}")
        if err_code == 'InvalidParameterException':
            status_code = 400
            resp = {
                'error': f'One of the resources in the request is invalid. Details : {err}'
            }
        else:
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
