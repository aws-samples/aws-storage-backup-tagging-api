from utils.api_gateway_response import DoubleQuoteDict
from utils.exceptions import InvalidRegionException


def is_region_valid(ec2_client, region):
    """This function checks whether the region is valid for all the services used in this lambda function.

    Args:
        ec2_client: The EC2 client authenticated for the account
        region: The region name that needs to be validated

    Returns:
      None

    Raises:
      InvalidRegionException: The exception indicating that the region name is inavlid.
    """
    response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in response['Regions']]
    if region not in regions:
        raise InvalidRegionException("Invalid region")


def get_caller_role(sts_client, iam_client):
    """This function returns the role name using which this function is creating resources in the account

    Args:
        sts_client: The STS client authenticated for the account
        iam_client: The IAM client authenticated for the account

    Returns:
      role_arn: The arn for the account
      aws_account_id: The aws account id the lambda function is running in
    """
    response = sts_client.get_caller_identity()
    arn = response.get('Arn')
    assumed_role_name_with_session = arn.split(":")[5]
    role_name = assumed_role_name_with_session.split("/")[1]
    aws_account_id = response.get('Account')
    get_role_response = iam_client.get_role(
        RoleName=role_name
    )
    role_arn = get_role_response.get('Role').get('Arn')
    return role_arn, aws_account_id


def filter_resource_arns(storage_resources_arn_list, resources_to_skip_arn_list):
    """Filter the list of all the storage resources in the account. Resource ARNs that have the skip-vpcx-backup

    Args:
        storage_resources_arn_list: The list of all the storage resource arns
        resources_to_skip_arn_list: The list of the resource arns that should be skipped

    Returns:
      The list of the resources that need to tagges with the vpcx-backup tag
    """
    for resource in resources_to_skip_arn_list:
        storage_resources_arn_list.remove(resource)
    return storage_resources_arn_list


def lambda_returns(status_code, headers, body):
    """Create a dictionary per ApiGateway's requirements

    Args:
        status_code(int): response.status_code
        headers(dict): response.headers
        body(str): response.text

    Returns:
        ret_object : specified by aws ApiGateway
    """
    headers = DoubleQuoteDict(headers)
    ret_object = {
        'statusCode': status_code,
        'headers': headers,
        'body': body
    }
    return ret_object
