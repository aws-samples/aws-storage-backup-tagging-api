import botocore.exceptions


def get_all_resources_to_skip(resource_tagging_client):
    """Get all the storage resources in the account filtered by the tag key `skip-vpcx-backup` and tag value `true`
    Args:
        resource_tagging_client: ResourceGroupsTaggingAPI client that is authenticated for the account.

    Returns:
      The list of the resource arns that needs to be skipped for tagging with vpcx-backup tag

    Raises:
      ClientError: Error from boto3.
    """
    resources_to_skip_arn_list = []
    try:
        paginator = resource_tagging_client.get_paginator('get_resources')
        response_iterator = paginator.paginate(
            ResourceTypeFilters=[
                'rds:cluster',
                'rds:db',
                'rds:global-cluster',
                'rds:ri',
                'dynamodb:table',
                'dynamodb:global-table',
                'elasticfilesystem:file-system',
                'fsx:file-system',
                'ec2:snapshot'
            ],
            TagFilters=[
                {
                    'Key': 'vpcx-skip-backup',
                    'Values': ['true']
                }
            ]
        )
        for page in response_iterator:
            for resource in page.get('ResourceTagMappingList', []):
                resources_to_skip_arn_list.append(resource.get('ResourceARN'))
        return resources_to_skip_arn_list
    except botocore.exceptions.ClientError:
        raise


def tag_storage_resources(resource_tagging_client, tag_list, resource_arn_list):
    """Tag the storage resources with the tag list
    Args:
        resource_tagging_client: ResourceGroupsTaggingAPI client that is authenticated for the account.
        tag_list: The list of the tags that needs to be applied on resources.
        resource_arn_list: The list of the resource arns that has to be tagged.

    Returns:
      None

    Raises:
      ClientError: Error from boto3.
    """
    try:
        for i in range(0, len(resource_arn_list), 20):
            resource_tagging_client.tag_resources(
                ResourceARNList=resource_arn_list[i:i+20],
                Tags=tag_list
            )
    except botocore.exceptions.ClientError:
        raise


def untag_storage_resources_to_skip(resource_tagging_client, resources_to_skip_arn_list, tag_keys):
    """Untag all the resources that should be skipped by the AWS Backups backup management.
    Args:
        resource_tagging_client: ResourceGroupsTaggingAPI client that is authenticated for the account.
        resources_to_skip_arn_list: Resources that should be untagged with vpcx-backup tag key.
        tag_keys: The tag keys which should be removed from the resource list

    Returns:
      None

    Raises:
      ClientError: Error from boto3.
    """
    try:
        for i in range(0, len(resources_to_skip_arn_list), 20):
            resource_tagging_client.untag_resources(
                ResourceARNList=resources_to_skip_arn_list[i:i+20],
                TagKeys=tag_keys
            )
    except botocore.exceptions.ClientError:
        raise


def get_tag_values_for_resources(resource_tagging_client, tag_key):
    """Get tag values for a tag key for all the given resource arns

    Args:
        resource_tagging_client: ResourceGroupsTaggingAPI authenticated client for the account
        tag_key: The key for which values are to be retrieved

    Returns:
        tag_values: Values for the tag keys

    Raises:
        ClientError: boto3 client error
    """
    try:
        tag_values = []
        paginator = resource_tagging_client.get_paginator('get_tag_values')
        response_iterator = paginator.paginate(
            Key=tag_key
        )
        for page in response_iterator:
            for tag_value in page.get('TagValues', []):
                tag_values.append(tag_value)
        return tag_values
    except botocore.exceptions.ClientError:
        raise
