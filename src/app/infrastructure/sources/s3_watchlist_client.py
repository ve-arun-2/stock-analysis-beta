"""
S3-backed watchlist workbook access.

Fetches and saves the watchlist Excel workbook from/to S3 — used by both
excel_source.py (reads + writes it) and stock_monitor.py (reads it), so
there's one place that knows the bucket/key and talks to S3, instead of
duplicating boto3 calls. The workbook is never written to local disk —
just held in memory (BytesIO) for as long as it's being read or built.
"""

from io import BytesIO

from app.core.aws_credentials import AwsCredentials
from app.core.config import settings

aws_credentials = AwsCredentials()

WATCHLIST_KEY = "My-watchlist-stocks.xlsx"


def download_watchlist() -> BytesIO:
    """Fetch the watchlist workbook from S3 into an in-memory buffer."""
    s3 = aws_credentials.s3Client()
    response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=WATCHLIST_KEY)
    return BytesIO(response["Body"].read())


def upload_watchlist(buffer: BytesIO) -> None:
    """Upload the (updated) watchlist workbook back to the same S3 key."""
    buffer.seek(0)
    s3 = aws_credentials.s3Client()
    s3.put_object(Bucket=settings.S3_BUCKET_NAME, Key=WATCHLIST_KEY, Body=buffer.read())
