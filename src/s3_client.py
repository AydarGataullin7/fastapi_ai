async def upload_file_o_s3(  # noqa: PLR0913, PLR0917
        client,
        body: bytes,
        key: str,
        bucket: str,
        endpoint: str,
        content_type: str = "text/html",
        content_disposition: str = "inline",
) -> str:
    await client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
        ContentDisposition=content_disposition,
    )
    return f"http://{endpoint}/{bucket}/{key}"
