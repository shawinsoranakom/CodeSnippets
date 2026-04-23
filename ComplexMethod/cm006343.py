async def list_files(self, flow_id: str) -> list[str]:
        """List all files in a specified S3 prefix (flow namespace).

        Args:
            flow_id: The flow/user identifier for namespacing

        Returns:
            list[str]: A list of file names (without the prefix)

        Raises:
            Exception: If there's an error listing files from S3
        """
        if not isinstance(flow_id, str):
            flow_id = str(flow_id)

        prefix = self.build_full_path(flow_id, "")

        try:
            async with self._get_client() as s3_client:
                paginator = s3_client.get_paginator("list_objects_v2")
                files = []

                async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            # Extract just the filename (remove the prefix)
                            full_key = obj["Key"]
                            # Remove the flow_id prefix to get just the filename
                            file_name = full_key[len(prefix) :]
                            if file_name:  # Skip the directory marker if it exists
                                files.append(file_name)

        except Exception:
            logger.exception(f"Error listing files in S3 flow {flow_id}")
            raise
        else:
            return files