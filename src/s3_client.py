

async def upload_file_o_s3(  # noqa: PLR0913, PLR0917
        client,
        file_path: str,
        key: str,
        bucket: str,
        endpoint: str,
        content_type: str = "text/html",
        content_disposition: str = "inline",
) -> str:
    with open(file_path, "rb") as f:
        file_content = f.read()

    await client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_content,
        ContentType=content_type,
        ContentDisposition=content_disposition,
    )
    return f"http://{endpoint}/{bucket}/{key}"
