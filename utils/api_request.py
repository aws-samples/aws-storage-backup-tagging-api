"""This module is used to do API calls to AWSAPI Microservices"""
# pylint:disable= no-member, invalid-name, E0401, W1203, C0411
from requests import request as req
from flask import Response
import logging
import os
import boto3
from azureauth.create_token import TokenGenerator

HTTP_GET = 'get'
HTTP_PUT = 'put'
HTTP_POST = 'post'

lgr = logging.getLogger()
lgr.setLevel(logging.INFO)


class ApiRequests:
    """Class for Making AWSAPI Microservice Calls"""

    def __init__(self, logger=None):
        """
        Setup for ApiRequests Class
        """
        self.logger = logger
        if not self.logger:
            self.logger = lgr
        self.token_url = os.environ.get("token_url")
        self.client_id = os.environ.get("RESOURCE_TAGGING_CLIENT_ID")
        secret_name = os.environ.get('RESOURCE_TAGGING_SECRET_NAME', 'nextbot/resource_tagging')
        region = os.environ.get('region', 'us-east-1')
        self.client_secret = (
            os.environ.get('RESOURCE_TAGGING_SECRET_VALUE') if os.environ.get('RESOURCE_TAGGING_SECRET_VALUE')
            else boto3.client('secretsmanager', region).get_secret_value(SecretId=secret_name).get('SecretString')
        )
        os.environ['RESOURCE_TAGGING_SECRET_VALUE'] = self.client_secret
        self.logger.info(f"The secret retrieved from secrets_manager: {self.client_secret}")

    def get_access_token(self, client_id: str = None, client_secret: str = None, scope: str = None) -> str:
        """
        Get an Access Token for the <scope> of the client

        Args:
            client_id (str): client id to get token.
            client_secret (str): client secret to get token.
            scope (str): Azure AD App registration scope | DEFAULT = VPCxIAM Default Scope.

        Returns:
            str: Azure AD Bearer Token
        """
        if not scope:
            scope = self.scope
        if not client_id:
            client_id = self.client_id
        if not client_secret:
            client_secret = self.client_secret
        try:
            self.logger.info(f"Generating Bearer token for scope '{scope}'.")
            generator = TokenGenerator(client_id, client_secret, token_url=self.token_url)
            token = generator.get_bearer_token(scope)
        except Exception as ex:
            self.logger.error(
                f"get_access_token - Failed to generated token for scope {scope} at url {self.token_url}."
                f" Error Details - {str(ex)}."
            )
            raise ex
        return token

    def request(
            self, url: str, method: str,
            scope: str = None, additional_headers: dict = None,
            additional_payload: dict = None
    ) -> Response:
        """
        Make a Http request to the provided url

        Args:
            url (str): API URL.
            method (str): Http method. Values = 'get'
            scope (str): AWSAPI Microservice scope for registered Azure App.
            additional_headers (dict): Additional request headers.
            additional_payload (dict): Additional request paylaod.

        Returns:
            Response: Response object of Http Request
        """
        try:
            access_token = self.get_access_token(scope=scope)
            headers = {
                "Content-Type": "application/json",
                "Authorization": access_token
            }
            if additional_headers:
                headers.update(additional_headers)
            kwargs = {
                "verify": False,
                "headers": headers
            }
            payload = {}
            if additional_payload:
                payload.update(additional_payload)
            if method in [HTTP_PUT, HTTP_POST]:
                kwargs["json"] = payload
            elif method in [HTTP_GET]:
                kwargs["params"] = payload
            else:
                raise Exception(f"Http Method type {method} not Supported")
            self.logger.info(
                f"Making {method.upper()} call - "
                "{"
                f"'url': '{url}', 'payload': {payload}"
                "}"
            )
            return req(method, url, timeout=300, **kwargs)
        except Exception as ex:
            self.logger.error(
                f"get_access_token - Failed to generated token for scope {scope}."
                f" Error Details - {str(ex)}."
            )
            raise ex
