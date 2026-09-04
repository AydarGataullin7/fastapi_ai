import aioboto3
from botocore.config import Config


async def upload_file_o_s3(  # noqa: PLR0913, PLR0917
        file_path: str,
        key: str,
        bucket: str,
        endpoint: str,
        access_key: str,
        secret_key: str,
        content_type: str = "text/html",
        content_disposition: str = "inline",
) -> str:
    with open(file_path, "rb") as f:
        file_content = f.read()
    config = Config()
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=config,
    ) as client:
        await client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_content,
            ContentType=content_type,
            ContentDisposition=content_disposition,
        )
    return f"http://{endpoint}/{bucket}/{key}"
