"""Utilities for sending review invitation SMS messages."""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from portfolio_cum_blog import settings

logger = logging.getLogger(__name__)


def build_review_message(message_template, review_link, recipient_name=""):
    """Render the message template with link and optional recipient name."""
    resolved_template = (message_template or "").strip()
    if not resolved_template:
        resolved_template = "Hi {name}, please share your feedback here: {link}"
    message = resolved_template.replace("{name}", recipient_name or "there")
    message = message.replace("{link}", review_link)
    if review_link not in message:
        message = f"{message}\n{review_link}"
    return message


def send_review_sms(phone_number, message_body):
    """Send a review invitation through AWS End User Messaging SMS."""
    client = boto3.client(
        "pinpoint-sms-voice-v2",
        region_name=getattr(settings, "AWS_REGION", None),
    )

    request_data = {
        "DestinationPhoneNumber": phone_number,
        "MessageBody": message_body,
        "MessageType": getattr(
            settings, "AWS_EUM_DEFAULT_MESSAGE_TYPE", "TRANSACTIONAL"
        ),
    }

    sender_id = getattr(settings, "AWS_EUM_ORIGINATION_IDENTITY", "")
    if sender_id:
        request_data["OriginationIdentity"] = sender_id

    configuration_set = getattr(settings, "AWS_EUM_CONFIGURATION_SET_NAME", "")
    if configuration_set:
        request_data["ConfigurationSetName"] = configuration_set

    protect_configuration = getattr(settings, "AWS_EUM_PROTECT_CONFIGURATION_ID", "")
    if protect_configuration:
        request_data["ProtectConfigurationId"] = protect_configuration

    try:
        response = client.send_text_message(**request_data)
        logger.info(
            "Sent review SMS to %s using AWS End User Messaging",
            phone_number,
        )
        return response
    except (ClientError, BotoCoreError) as err:
        logger.exception("Failed to send review SMS to %s", phone_number)
        raise err
