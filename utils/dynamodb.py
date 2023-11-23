import botocore.exceptions


def get_dynamodb_tables(dynamodb_client, region):
    """List all the DynamoDB tables. From the table names describe and get the ARN

    Args:
        dynamodb_client: The DynamoDB client authenticated for the account
        regio: The region in which the dynamodb tables have to be tagged

    Returns:
      The list of dynamodb table arns that need to be tagged with the vpcx-backup tag

    Raises:
      ClientError: Error from boto3.ed.
    """
    try:
        dynamodb_table_names = []
        dynamodb_table_arns = []
        dynamodb_global_table_names = []
        dynamodb_global_table_arns = []

        # Get the table names.
        paginator = dynamodb_client.get_paginator('list_tables')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for table_name in page.get('TableNames', []):
                dynamodb_table_names.append(table_name)

        for table_name in dynamodb_table_names:
            response = dynamodb_client.describe_table(
                TableName=table_name
            )
            dynamodb_table_arns.append(response.get('Table', {}).get('TableArn'))

        # Get the global table names
        response = dynamodb_client.list_global_tables(
            RegionName=region
        )
        exclusive_start_global_table_name = response.get('LastEvaluatedGlobalTableName', None)
        for global_table in response.get('GlobalTables', []):
            dynamodb_global_table_names.append(global_table.get('GlobalTableName'))
        # Paginate for the remaining responses.
        while exclusive_start_global_table_name is not None:
            response = dynamodb_client.list_global_tables(
                ExclusiveStartGlobalTableName=exclusive_start_global_table_name,
                RegionName=region
            )
            exclusive_start_global_table_name = response.get('LastEvaluatedGlobalTableName', None)
            for global_table in response.get('GlobalTables', []):
                dynamodb_global_table_names.append(global_table.get('GlobalTableName'))

        # Get the global table ARNs
        for global_table_name in dynamodb_global_table_names:
            response = dynamodb_client.describe_global_table(
                GlobalTableName=global_table_name
            )
            dynamodb_global_table_arns.append(response.get('GlobalTableDescription').get('GlobalTableArn'))

        # Combine the list of ARNs to have a common list of the DynamoDB ARNs to tag
        return dynamodb_table_arns + dynamodb_global_table_arns
    except botocore.exceptions.ClientError:
        raise
