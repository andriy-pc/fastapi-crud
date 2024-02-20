import json
import logging

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore

from simplecrud.settings import get_aws_settings

_session = boto3.session.Session()
_client = _session.client(
    service_name="secretsmanager",
    region_name=get_aws_settings().region,
)


log = logging.getLogger(__name__)


async def get_string_secret(key: str) -> str:
    try:
        get_secret_value_response = _client.get_secret_value(
            SecretId=get_aws_settings().secret_name
        )
    except ClientError as e:
        error_message = ""
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            error_message = (
                f"The requested secret {get_aws_settings().secret_name} was not found"
            )
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            error_message = "The request was invalid due to exception"
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            error_message = "The request had invalid params"
        elif e.response["Error"]["Code"] == "DecryptionFailure":
            error_message = (
                "The requested secret can't be decrypted using the provided KMS key"
            )
        elif e.response["Error"]["Code"] == "InternalServiceError":
            error_message = "An error occurred on service side"

        raise ValueError(error_message, e)
    else:
        secrets_dict: dict[str, str] = json.loads(
            get_secret_value_response["SecretString"]
        )
        return secrets_dict[key]
