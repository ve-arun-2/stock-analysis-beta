import boto3
from app.core.config import settings

class AwsCredentials:
  def __init__(self):
    self._session = boto3.Session(
        region_name =settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )

  def s3Client(self):
    return self._session.client("s3")

  def sqsClient(self):
    return self._session.client("sqs")
