import botocore.exceptions


def get_efs_file_systems(efs_client):
    """Get the ARNs for all the EFS snapshots in the account.

    Args:
        efs_client: The EFS client authenticated for the account

    Returns:
      The list of EFS file systems arns to be tagged with the vpcx-backup tag

    Raises:
      ClientError: Error from boto3.
    """
    try:
        efs_arns = []
        paginator = efs_client.get_paginator('describe_file_systems')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for file_system in page.get('FileSystems', []):
                efs_arns.append(file_system.get('FileSystemArn'))
        return efs_arns
    except botocore.exceptions.ClientError:
        raise
