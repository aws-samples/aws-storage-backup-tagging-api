import botocore.exceptions


def get_redshift_cluster_arns(redshift_client, region, account):
    """Get ANRs for all the Redshift Clusters in the account

    Args:
        redshift_client: Redshift client that is authenticated for the account.
        region: The region in which the redshift clusters are deployed
        account: The unique AWS account id

    Returns:
      The list of redshift arns that have to be tagged

    Raises:
      ClientError: Error from boto3.
    """
    try:
        redshift_cluster_arns = []
        paginator = redshift_client.get_paginator('describe_clusters')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for cluster in page.get('Clusters', []):
                cluster_arn = f"arn:aws:redshift:{region}:{account}:cluster:{cluster.get('ClusterIdentifier')}"
                redshift_cluster_arns.append(cluster_arn)
        return redshift_cluster_arns
    except botocore.exceptions.ClientError:
        raise
