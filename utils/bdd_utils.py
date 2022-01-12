import botocore.exceptions
import boto3


def create_rds_instance(rds_client, subnet_group_name):
    """
    Create an RDS instance and wait until the instance is in available state. Return the RDS instance identifier

    Args:
        rds_client: The RDS authenticated client
        subnet_group_name: The DB subnet group name that the DB instance should reside in

    Returns:
      rds_instance_identifier: The RDS DB instance identifier
      rds_instance_arn: The ARN of the RDS DB instance

    Raises:
      ClientError: Error from boto3.
    """
    try:
        response = rds_client.create_db_instance(
            DBName='bddtest',
            DBInstanceIdentifier="bdd-test",
            DBInstanceClass="db.m4.large",
            Engine="mysql",
            MasterUsername="admin",
            AllocatedStorage=32,
            MasterUserPassword="Welcome123456",
            DBSubnetGroupName=subnet_group_name,
        )
        rds_instance_identifier = response.get('DBInstance').get('DBInstanceIdentifier')
        rds_instance_arn = response.get('DBInstance').get('DBInstanceArn')
        db_instance_waiter = rds_client.get_waiter('db_instance_available')
        db_instance_waiter.wait(
            DBInstanceIdentifier=rds_instance_identifier,
            WaiterConfig={
                'Delay': 45
            }
        )
        return rds_instance_identifier, rds_instance_arn
    except botocore.exceptions.ClientError:
        raise


def destroy_rds_instance(rds_client, db_instance_identifier):
    """Destroy an RDS instance given the DB instance identifier
    Args:
        rds_client: The RDS authenticated client
        db_instance_identifier: The RDS DB instance identifier

    Returns:
      None

    Raises:
      ClientError: Error from boto3.
    """
    try:
        rds_client.delete_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
        waiter = rds_client.get_waiter('db_instance_deleted')
        waiter.wait(
            DBInstanceIdentifier=db_instance_identifier
        )
    except botocore.exceptions.ClientError:
        raise


def create_dynamodb_table(dynamodb_client):
    """Create a dynamodb table for the BDD testing

    Args:
        dynamodb_client: The DynamoDB authenticated client

    Returns:
      DynamoDB table name
      DynamoDB table arn

    Raises:
      ClientError: Error from boto3.
    """
    response = dynamodb_client.create_table(
        AttributeDefinitions=[{
            'AttributeName': 'TestKey',
            'AttributeType': 'S'
        }],
        TableName='BDD_Test_Table',
        KeySchema=[
            {
                'AttributeName': 'TestKey',
                'KeyType': 'HASH'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    try:
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(
            TableName=response.get('TableDescription').get('TableName'),
            WaiterConfig={
                'Delay': 45
            }
        )
        return response.get('TableDescription').get('TableName'), response.get('TableDescription').get('TableArn')
    except botocore.exceptions.ClientError:
        raise


def destroy_dynamodb_table(dynamodb_client, dynamodb_table_name):
    """Destroy a dynamodb table for the given table name.

    Args:
        dynamodb_client: The DynamoDB authenticated client
        dynamodb_table_name: The dynamodb table name

    Returns:
      None

    Raises:
      ClientError: Error from boto3.
    """
    try:
        dynamodb_client.delete_table(
            TableName=dynamodb_table_name
        )
        waiter = dynamodb_client.get_waiter('table_not_exists')
        waiter.wait(
            TableName=dynamodb_table_name
        )
    except botocore.exceptions.ClientError:
        raise


def create_fsx_file_system(fsx_client, subnet_id, security_group_id):
    """Create FSx file systems for Windows and Lustre

    Args:
        fsx_client: The FSX client authenticated for the account
        subnet_id: The id of the subnet the FSX file system should be deployed in
        security_group_id: The id of the security group that will be applied to the FSX file system

    Returns:
      FSX file system id
      FSX file system arn

    Raises:
      ClientError: Error from boto3.
    """
    try:
        response = fsx_client.create_file_system(
            FileSystemType='LUSTRE',
            StorageCapacity=1200,
            SubnetIds=[subnet_id],
            SecurityGroupIds=[security_group_id],
            Tags=[{
                'Key': 'Name',
                'Value': 'BDD-TEST-FS'
            }]
        )
        file_system_id = response.get('FileSystem').get('FileSystemId')
        file_system_arn = response.get('FileSystem').get('ResourceARN')
        return file_system_id, file_system_arn
    except botocore.exceptions.ClientError:
        raise


def destroy_fsx_file_system(fsx_client, file_system_id):
    """Destroy the FSx file system.

    Args:
        fsx_client: The FSX client authenticated for the account
        file_system_id: The id of the file system that has to be deleted

    Returns:
      None

    Raises:
      ClientError: Error from boto3.
    """
    try:
        fsx_client.delete_file_system(
            FileSystemId=file_system_id
        )
    except botocore.exceptions.ClientError:
        raise


def create_ebs_volume(ec2_client):
    """Create an EBS volume.
    Args:
        ec2_client: The authenticated EC2 client for the test account

    Returns:
      volume_id: The id of the volume that is created

    Raises:
      ClientError: Error from boto3.
    """
    try:
        response = ec2_client.create_volume(
            AvailabilityZone='us-east-1a',
            Encrypted=True,
            Size=16,
            VolumeType='gp2'
        )
        waiter = ec2_client.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[
                response.get('VolumeId')
            ]
        )
        return response.get('VolumeId')
    except botocore.exceptions.ClientError:
        raise


def destroy_ebs_volume(ec2_client, volume_id):
    """Destroy an EBS volume
    Args:
        ec2_client: The authenticated EC2 client for the test account
        volume_id: The volume id that needs to be destroyed

    Returns:
        None

    Raises:
        ClientError: Error from boto3
    """
    try:
        ec2_client.delete_volume(
            VolumeId=volume_id,
        )
        waiter = ec2_client.get_waiter('volume_deleted')
        waiter.wait(
            VolumeIds=[
                volume_id
            ]
        )
    except botocore.exceptions.ClientError:
        raise


def create_efs_file_system(efs_client):
    """Create EFS file system to test for BDD

    Args:
        efs_client: EFS client authenticated for the test account

    Returns:
        file_system_id: The id of the file system created.
        file_system_arn: The ARN of the file system created.

    Raises:
        ClientError: Boto3 error
    """
    try:
        response = efs_client.create_file_system(
            Tags=[{
                'Key': 'Name',
                'Value': 'BDD-TEST-FS'
            }]
        )
        return response.get('FileSystemId')
    except botocore.exceptions.ClientError:
        raise


def destroy_efs_file_system(efs_client, file_system_id):
    """Destroy the EFS file system

    Args:
        efs_client: The authenticated EFS client for the test account
        file_system_id: The id of the file system that has to be deleted

    Returns:
        None

    Raises:
        ClientError: boto3 error
    """
    try:
        efs_client.delete_file_system(
            FileSystemId=file_system_id
        )
    except botocore.exceptions.ClientError:
        raise


def create_redshift_cluster(redshift_client, db_security_group, subnet_id):
    """Create Redshift cluster

    Args:
        redshift_client: Authenticated redshift client for the test account
        db_security_group: Security group for the Redshift cluster

    Returns:
        cluster_arn: The ARN of the created redshift cluster
        cluster_identifier: The unique name of the cluster
        subnet_id: The subnet with which a cluster subnet group will be created.

    Raises:
        ClientError: boto3 error
    """
    try:
        # Create a Redshift cluster subnet group.
        response = redshift_client.create_cluster_subnet_group(
                        ClusterSubnetGroupName='bddTestSubnetGroup',
                        Description='BDD test Redshift cluster subnet group',
                        SubnetIds=[
                            subnet_id,
                        ]
                    )
        cluster_subnet_group_name = response.get('ClusterSubnetGroup').get('ClusterSubnetGroupName')
        response = redshift_client.create_cluster(
            ClusterIdentifier='Put-Tags-BDD-Test',
            ClusterType='single-node',
            NodeType='ds2.xlarge',
            MasterUsername='bdd_test',
            MasterUserPassword='bddTest123',
            ClusterSubnetGroupName=cluster_subnet_group_name,
            VpcSecurityGroupIds=[
                db_security_group,
            ]
        )
        waiter = redshift_client.get_waiter('cluster_available')
        waiter.wait(
            ClusterIdentifier='Put-Tags-BDD-Test'
        )
        return cluster_subnet_group_name, \
               response.get('Cluster').get('ClusterNamespaceArn'), \
               response.get('Cluster').get('ClusterIdentifier')
    except botocore.exceptions.ClientError:
        raise


def destroy_redshift_cluster(redshift_client, cluster_identifier, cluster_subnet_group_name):
    """Destroy the redshift cluster

    Args:
        redshift_client: The Redshift authenticated client for the test account
        cluster_identifier: The unique identifier of the redshift cluster that has to be deleted
        cluster_subnet_group_name: The name of the redshift cluster subnet group that has to be deleted after cluster
        deletion

    Returns:
        None

    Raises:
        ClientError: boto3 error
    """
    try:
        redshift_client.delete_cluster(
            ClusterIdentifier=cluster_identifier,
            SkipFinalClusterSnapshot=True
        )
        waiter = redshift_client.get_waiter('cluster_deleted')
        waiter.wait(
            ClusterIdentifier=cluster_identifier
        )
        redshift_client.delete_cluster_subnet_group(
            ClusterSubnetGroupName=cluster_subnet_group_name
        )
    except botocore.exceptions.ClientError:
        raise


def boto3_client(creds, service, region):
    """
    Function to get boto3 client for a specific service.
    Args:
        creds (object): Credentials for the account
        service(str): Name of the aws service.
        region: The region for which boto3 client has to be initialized
    Returns:
        object: client object

    """
    credentials = creds.get('credentials', {})
    region = region
    client = boto3.client(
        service_name=service,
        region_name=region,
        aws_access_key_id=credentials.get('AccessKeyId', ''),
        aws_secret_access_key=credentials.get('SecretAccessKey', ''),
        aws_session_token=credentials.get('SessionToken', ''))
    return client
