import botocore.exceptions


def tag_all_ebs_volumes(ec2_client, tag_list, vpcx_backup_tag):
    """
    Tag all the EBS volumes in the account. Volumes ANRs can't be queried through boto3 ec2_client, hence they have
    to be tagged using the ec2_client instead of the resourcegroupstaggingapi

    :param ec2_client: The authenticated ec2 client for the account
    :param tag_list: The tag list that has to be applied on the EBS volumes
    :param vpcx_backup_tag: The vpcx_backup_tag that should be applied on the EBS volumes
    """
    try:
        volume_ids = []
        volume_ids_to_skip = []

        # Get all the volume ids in the account.
        paginator = ec2_client.get_paginator('describe_volumes')
        response_iterator = paginator.paginate()
        for page in response_iterator:
            for volume in page.get('Volumes', []):
                volume_ids.append(volume.get('VolumeId'))

        # Skip volumes if the vpcx-backup tag value is not legal-hold
        if vpcx_backup_tag:
            if vpcx_backup_tag["vpcx-backup"] != "legal-hold":
                # Can skip the volumes with skip backups tag
                response_iterator = paginator.paginate(
                    Filters=[
                        {
                            'Name': 'tag:vpcx-skip-backup',
                            'Values': ['true']
                        }
                    ]
                )
                for page in response_iterator:
                    for volume in page.get('Volumes', []):
                        volume_ids_to_skip.append(volume.get('VolumeId'))

        # Filter the volumes ids to tag
        volume_ids_vpcx_backup_tag = volume_ids
        for volume_id in volume_ids_to_skip:
            volume_ids_vpcx_backup_tag.remove(volume_id)

        # Tag using the EC2 create-tags API. Attempt to tag 1000 volume ids in each iteration as 1000 ResourceIds at
        # a time is the API limitation.
        # More details here:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_tags
        tags = []
        for key in tag_list:
            tags.append({
                'Key': key,
                'Value': tag_list.get(key)
            })
        if len(tags) != 0:
            # Tag only if there is at least 1 tag in the tag list.
            for i in range(0, len(volume_ids), 1000):
                ec2_client.create_tags(
                    Resources=volume_ids[i:i+1000],
                    Tags=tags
                )

        if len(vpcx_backup_tag.keys()) != 0:
            # Tag the volumes with vpcx-backup tag
            for i in range(0, len(volume_ids_vpcx_backup_tag), 1000):
                ec2_client.create_tags(
                    Resources=volume_ids_vpcx_backup_tag[i:i+1000],
                    Tags=[
                        {
                            'Key': 'vpcx-backup',
                            'Value': vpcx_backup_tag.get('vpcx-backup')
                        }
                    ]
                )

    except botocore.exceptions.ClientError:
        raise


def tag_untag_skip_backup_ebs_volumes(ec2_client, volume_ids, tag_list):
    """Tag given ebs volume ids with the vpcx-skip-backup tag. Once tagged, untag with the vpcx-backup so that
       AWS Backups skips these volumes

    Args:
        ec2_client: The authenticated ec2_client for the account
        volume_ids: The ids of all the volumes that should be tagged with skip backup
        tag_list: the tag list that should be added to the volumes

    Returns:
        None

    Raises:
        ClientError: boto3 client error
    """
    try:
        for i in range(0, len(volume_ids), 1000):
            ec2_client.create_tags(
                Resources=volume_ids[i:i+1000],
                Tags=[{'Key': k, 'Value': v} for (k, v) in tag_list.items()]
            )
            ec2_client.delete_tags(
                Resources=volume_ids[i:i+1000],
                Tags=[
                    {
                        'Key': 'vpcx-backup',
                        'Value': 'regular'
                    },
                ]
            )
    except botocore.exceptions.ClientError:
        raise
