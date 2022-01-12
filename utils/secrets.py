import json


def retrieve_ldap_password(secrets_manager_client, logger, ldap_password_secret_name):
    """
    Retrieve LDAP service account password from secrets manager

    Expected password format:
    {
        "PASSWORD": "service_account_password"
    }

    Returns:
        str: plaintext ldap password
    """
    logger.info("Retrieving LDAP service account password from Secrets Manager")
    secret_response = secrets_manager_client.get_secret_value(
        SecretId=str(ldap_password_secret_name)
    )
    return json.loads(secret_response['SecretString'])['PASSWORD']
