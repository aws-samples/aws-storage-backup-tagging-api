import botocore.exceptions


def get_fsx_file_systems(fsx_client):
    """Get all the ARNs for all the FSx file systems in the account.

    Args:
        fsx_client: The FSX client authenticated for the account.

    Returns:
      The list of FSX file systems arns that has to be tagged with vpcx-backup tag

    Raises:
      ClientError: Error from boto3.
    """
    try:
        fsx_file_system_arns = []
        paginator = fsx_client.get_paginator('describe_file_systems')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for file_system in page.get('FileSystems', []):
                fsx_file_system_arns.append(file_system.get('ResourceARN'))
        return fsx_file_system_arns
    except botocore.exceptions.ClientError:
        raise
