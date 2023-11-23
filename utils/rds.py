import botocore.exceptions


def get_rds_instances(rds_client):
    """Get the list of ANRs for rds instance and rds clusters.

    Args:
        rds_client: RDS client that is authenticated for the account.

    Returns:
      The list of the rds arns that needs to be tagged with vpcx-backup tag

    Raises:
      ClientError: Error from boto3.
    """
    try:
        rds_instance_anrs = []
        rds_cluster_arns = []
        rds_global_cluster_arns = []
        rds_reserved_instance_arns = []

        # Get all the db instance arns
        paginator = rds_client.get_paginator('describe_db_instances')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for db_instance in page.get('DBInstances', []):
                rds_instance_anrs.append(db_instance.get('DBInstanceArn'))

        # Get all the cluster arns
        paginator = rds_client.get_paginator('describe_db_clusters')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for db_cluster in page.get('DBClusters', []):
                rds_cluster_arns.append(db_cluster.get('DBClusterArn'))

        # Get all the global cluster arns
        paginator = rds_client.get_paginator('describe_global_clusters')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for global_cluster in page.get('GlobalClusters', []):
                rds_global_cluster_arns.append(global_cluster.get('GlobalClusterArn'))

        # Get all the reserved RDS instances
        paginator = rds_client.get_paginator('describe_reserved_db_instances')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for reserved_db_instance in page.get('ReservedDBInstances', []):
                rds_reserved_instance_arns.append((reserved_db_instance.get('ReservedDBInstanceArn')))

        # Return the combined list of all the RDS ARNs.
        return rds_instance_anrs + rds_cluster_arns + rds_global_cluster_arns + rds_reserved_instance_arns
    except botocore.exceptions.ClientError:
        raise
