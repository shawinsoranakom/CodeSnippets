async def _save_to_aws(self) -> Message:
        """Save file to AWS S3 using S3 functionality."""
        import os

        import boto3

        from lfx.base.data.cloud_storage_utils import create_s3_client, validate_aws_credentials

        # Get AWS credentials from component inputs or fall back to environment variables
        aws_access_key_id = getattr(self, "aws_access_key_id", None)
        if aws_access_key_id and hasattr(aws_access_key_id, "get_secret_value"):
            aws_access_key_id = aws_access_key_id.get_secret_value()
        if not aws_access_key_id:
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")

        aws_secret_access_key = getattr(self, "aws_secret_access_key", None)
        if aws_secret_access_key and hasattr(aws_secret_access_key, "get_secret_value"):
            aws_secret_access_key = aws_secret_access_key.get_secret_value()
        if not aws_secret_access_key:
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        bucket_name = getattr(self, "bucket_name", None)
        if not bucket_name:
            # Try to get from storage service settings
            settings = get_settings_service().settings
            bucket_name = settings.object_storage_bucket_name

        # Validate AWS credentials
        if not aws_access_key_id:
            msg = (
                "AWS Access Key ID is required for S3 storage. Provide it as a component input "
                "or set AWS_ACCESS_KEY_ID environment variable."
            )
            raise ValueError(msg)
        if not aws_secret_access_key:
            msg = (
                "AWS Secret Key is required for S3 storage. Provide it as a component input "
                "or set AWS_SECRET_ACCESS_KEY environment variable."
            )
            raise ValueError(msg)
        if not bucket_name:
            msg = (
                "S3 Bucket Name is required for S3 storage. Provide it as a component input "
                "or set LANGFLOW_OBJECT_STORAGE_BUCKET_NAME environment variable."
            )
            raise ValueError(msg)

        # Validate AWS credentials
        validate_aws_credentials(self)

        # Create S3 client
        s3_client = create_s3_client(self)
        client_config: dict[str, Any] = {
            "aws_access_key_id": str(aws_access_key_id),
            "aws_secret_access_key": str(aws_secret_access_key),
        }

        # Get region from component input, environment variable, or settings
        aws_region = getattr(self, "aws_region", None)
        if not aws_region:
            aws_region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION")
        if aws_region:
            client_config["region_name"] = str(aws_region)

        s3_client = boto3.client("s3", **client_config)

        # Extract content
        content = self._extract_content_for_upload()
        file_format = self._get_file_format_for_location("AWS")

        # Generate file path
        file_path = f"{self.file_name}.{file_format}"
        if hasattr(self, "s3_prefix") and self.s3_prefix:
            file_path = f"{self.s3_prefix.rstrip('/')}/{file_path}"

        # Create temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=f".{file_format}", delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Upload to S3
            s3_client.upload_file(temp_file_path, bucket_name, file_path)
            s3_url = f"s3://{bucket_name}/{file_path}"
            return Message(text=f"File successfully uploaded to {s3_url}")
        finally:
            # Clean up temp file
            if Path(temp_file_path).exists():
                Path(temp_file_path).unlink()