async def save_file(self, flow_id: str, file_name: str, data: bytes, *, append: bool = False) -> None:
        """Save a file to S3.

        Args:
            flow_id: The flow/user identifier for namespacing
            file_name: The name of the file to be saved
            data: The byte content of the file
            append: If True, append to existing file (not supported in S3, will raise error)

        Raises:
            Exception: If the file cannot be saved to S3
            NotImplementedError: If append=True (not supported in S3)
        """
        if append:
            msg = "Append mode is not supported for S3 storage"
            raise NotImplementedError(msg)

        key = self.build_full_path(flow_id, file_name)

        try:
            async with self._get_client() as s3_client:
                put_params: dict[str, Any] = {
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "Body": data,
                }

                if self.tags:
                    tag_string = "&".join([f"{k}={v}" for k, v in self.tags.items()])
                    put_params["Tagging"] = tag_string

                await s3_client.put_object(**put_params)

            await logger.ainfo(f"File {file_name} saved successfully to S3: s3://{self.bucket_name}/{key}")

        except Exception as e:
            error_msg = str(e)
            error_code = None

            if hasattr(e, "response") and isinstance(e.response, dict):
                error_info = e.response.get("Error", {})
                error_code = error_info.get("Code")
                error_msg = error_info.get("Message", str(e))

            logger.exception(f"Error saving file {file_name} to S3 in flow {flow_id}: {error_msg}")

            if error_code == "NoSuchBucket":
                msg = f"S3 bucket '{self.bucket_name}' does not exist"
                raise FileNotFoundError(msg) from e
            if error_code == "AccessDenied":
                msg = "Access denied to S3 bucket. Please check your AWS credentials and bucket permissions"
                raise PermissionError(msg) from e
            if error_code == "InvalidAccessKeyId":
                msg = "Invalid AWS credentials. Please check your AWS access key and secret key"
                raise PermissionError(msg) from e
            msg = f"Failed to save file to S3: {error_msg}"
            raise RuntimeError(msg) from e