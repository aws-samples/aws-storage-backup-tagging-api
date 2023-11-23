"""
this module contains behave framework function implementation
"""
# pylint:disable=no-name-in-module,import-error, C0413, C0411

import os
import sys
import boto3

sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '')))

THISDIR = os.path.dirname(__file__)  # bdd/
TESTDIR = os.path.dirname(THISDIR)  # tests/
LAMBDADIR = os.path.dirname(TESTDIR)  # storage_resource_tagging/
APPDIR = os.path.dirname(LAMBDADIR)  # resource-tagging/
SERVERLESSDIR = os.path.dirname(APPDIR)  # serverless_2/
ROOTDIR = os.path.dirname(SERVERLESSDIR)  # awsapi/

sys.path.insert(0, THISDIR)
sys.path.insert(0, TESTDIR)
sys.path.insert(0, LAMBDADIR)
sys.path.insert(0, SERVERLESSDIR)
sys.path.insert(0, ROOTDIR)

from tests import config, logger, shared_config
from serverless.bdd_utils import utils
from utils import bdd_utils


def before_all(context):
    """
    This method runs before all
    Args:
        context:
    Returns:
    """
    # environment variables for app

    logger.info("======================")
    logger.info("IN BEFORE")
    logger.info("======================")

    context.token_url = config['main']['token_url']
    context.account = config['main']['account']
    context.region = config['main']['region']
    context.application_endpoint = config['oauth2']['application_vpc_endpoint']
    context.application_scope = config['oauth2']['application_scope']
    context.application_account = config['main']['admin_account']
    context.test_account = config['main']['account']
    context.test_account_id = config['main']['account_id']
    context.stack_name = f"storage-resource-tagging-{config['main']['environment']}"
    context.client_id = shared_config['behave']['jenkins_client_id']
    context.client_secret = shared_config['behave']['jenkins_client_secret']
    context.creds_host = shared_config['behave']['creds_host']
    context.creds_endpoint = shared_config['behave']['creds_vpc_endpoint']
    context.creds_scope = shared_config['behave']['creds_scope']

    context.api_client = utils.ApiRequests(context.token_url, context.client_id, context.client_secret)
    admin_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                               scope=context.creds_scope, account=context.application_account)

    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)

    context.api_host = utils.get_serverless_api_host(context.stack_name,
                                                     context.application_account,
                                                     config['main']['environment'])
    logger.info(f"API HOST: {context.api_host}")
    context.resource_tagging_client = boto3_client(test_creds, 'resourcegroupstaggingapi')
    context.iam_client = boto3_client(test_creds, 'iam')
    context.sts_client = boto3_client(test_creds, 'sts')
    context.dynamodb_client = boto3_client(test_creds, 'dynamodb')
    context.ec2_client = boto3_client(test_creds, 'ec2')
    context.rds_client = boto3_client(test_creds, 'rds')
    context.fsx_client = boto3_client(test_creds, 'fsx')
    context.admin_sts_client = boto3_client(admin_creds, 'sts')
    context.admin_iam_client = boto3_client(admin_creds, 'iam')
    context.bdd_resource_arn_list = []

    # Tag list to be included in the API request body.
    context.bdd_tag_list = {
        'vpcx-backup': 'regular',
        'dummy-key': 'dummy-value'
    }

    # Get VPC, subnet and security group id
    context.vpc_id = config['behave']['vpc_id']
    context.subnet_id = config['behave']['subnet_id']
    context.db_security_group_id = config['behave']['db_security_group_id']
    context.db_subnet_group_name = config['behave']['db_subnet_group_name']
    context.file_share_security_group_id = config['behave']['file_share_security_group_id']
    # Create DynamoDB table
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.dynamodb_client = boto3_client(test_creds, 'dynamodb')
    context.dynamodb_table_name, dynamodb_table_arn = bdd_utils.create_dynamodb_table(context.dynamodb_client)

    # Create an RDS Instance
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.rds_client = boto3_client(test_creds, 'rds')
    context.rds_instance_identifier, rds_instance_arn = bdd_utils.create_rds_instance(context.rds_client,
                                                                                      context.db_subnet_group_name)

    # Create FSx file system
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.fsx_client = boto3_client(test_creds, 'fsx')
    context.fsx_file_system_id, fsx_file_system_arn = \
        bdd_utils.create_fsx_file_system(context.fsx_client,
                                         context.subnet_id,
                                         context.file_share_security_group_id)

    # Create EFS file system
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.efs_client = boto3_client(test_creds, 'efs')
    context.efs_file_system_id = bdd_utils.create_efs_file_system(context.efs_client)

    # Create EBS volume
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.ec2_client = boto3_client(test_creds, 'ec2')
    context.volume_id = \
        bdd_utils.create_ebs_volume(context.ec2_client)
    # Create Redshift cluster
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.redshift_client = boto3_client(test_creds, 'redshift')
    context.redshift_cluster_subnet_group_name, cluster_namespace_arn, context.cluster_identifier = \
        bdd_utils.create_redshift_cluster(context.redshift_client, context.db_security_group_id, context.subnet_id)

    # Append the ARNs to the ARN List for the resources created during this BDD.
    context.bdd_resource_arn_list.append(dynamodb_table_arn)
    context.bdd_resource_arn_list.append(rds_instance_arn)
    context.bdd_resource_arn_list.append(fsx_file_system_arn)
    context.bdd_resource_arn_list.append(
        f"arn:aws:elasticfilesystem:{context.region}:{context.test_account_id}:file-system/{context.efs_file_system_id}"
    )
    context.bdd_resource_arn_list.append(f"arn:aws:redshift:{context.region}:{context.test_account_id}:cluster:{context.cluster_identifier}")
    context.ebs_volumes_ids = [context.volume_id]


def boto3_client(creds, service):
    """
    Function to get boto3 client for a specific service.
    Args:
        creds (object): Credentials for the account
        service(str): Name of the aws service.
    Returns:
        object: client object

    """
    credentials = creds.get('credentials', {})
    region = config['main']['region']
    client = boto3.client(
        service_name=service,
        region_name=region,
        aws_access_key_id=credentials.get('AccessKeyId', ''),
        aws_secret_access_key=credentials.get('SecretAccessKey', ''),
        aws_session_token=credentials.get('SessionToken', ''))
    return client


def after_scenario(context, scenario):
    """
    This method is called after each scenario
    :param context:
    :param scenario:
    :return:
    """

    logger.info("======================")
    logger.info("CLEANING UP SCENARIO")
    logger.info("======================")


def after_all(context):
    """
    Cleanup all the resources created by the BDD for testing
    """
    # Delete the DynamoDB table
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.dynamodb_client = boto3_client(test_creds, 'dynamodb')
    bdd_utils.destroy_dynamodb_table(context.dynamodb_client, context.dynamodb_table_name)

    # Delete the RDS Instance
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.rds_client = boto3_client(test_creds, 'rds')
    bdd_utils.destroy_rds_instance(context.rds_client, context.rds_instance_identifier)

    # Delete the FSx file system
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.fsx_client = boto3_client(test_creds, 'fsx')
    bdd_utils.destroy_fsx_file_system(context.fsx_client, context.fsx_file_system_id)

    # Delete the EFS file system
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.efs_client = boto3_client(test_creds, 'efs')
    bdd_utils.destroy_efs_file_system(context.efs_client, context.efs_file_system_id)

    # Delete the EBS volume
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.ec2_client = boto3_client(test_creds, 'ec2')
    bdd_utils.destroy_ebs_volume(context.ec2_client, context.volume_id)

    # Delete the Redshift cluster
    test_creds = context.api_client.get_creds(url=context.creds_endpoint, host=context.creds_host,
                                              scope=context.creds_scope, account=context.test_account)
    context.redshift_client = boto3_client(test_creds, 'redshift')
    bdd_utils.destroy_redshift_cluster(context.redshift_client,
                                       context.cluster_identifier,
                                       context.redshift_cluster_subnet_group_name)
