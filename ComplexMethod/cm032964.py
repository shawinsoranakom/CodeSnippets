def _yield_blob_objects(
        self,
        start: datetime,
        end: datetime,
    ) -> GenerateDocumentsOutput:
        """Generate bucket objects"""
        if self.s3_client is None:
            raise ConnectorMissingCredentialError("Blob storage")

        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

        # Collect all objects first to count filename occurrences
        all_objects = []
        for page in pages:
            if "Contents" not in page:
                continue
            for obj in page["Contents"]:
                if obj["Key"].endswith("/"):
                    continue
                last_modified = obj["LastModified"].replace(tzinfo=timezone.utc)
                if start < last_modified <= end:
                    all_objects.append(obj)

        # Count filename occurrences to determine which need full paths
        filename_counts: dict[str, int] = {}
        for obj in all_objects:
            file_name = os.path.basename(obj["Key"])
            filename_counts[file_name] = filename_counts.get(file_name, 0) + 1

        batch: list[Document] = []
        for obj in all_objects:
            last_modified = obj["LastModified"].replace(tzinfo=timezone.utc)
            file_name = os.path.basename(obj["Key"])
            key = obj["Key"]

            size_bytes = extract_size_bytes(obj)
            if (
                self.size_threshold is not None
                and isinstance(size_bytes, int)
                and size_bytes > self.size_threshold
            ):
                logging.warning(
                    f"{file_name} exceeds size threshold of {self.size_threshold}. Skipping."
                )
                continue

            try:
                blob = download_object(self.s3_client, self.bucket_name, key, self.size_threshold)
                if blob is None:
                    continue

                # Use full path only if filename appears multiple times
                if filename_counts.get(file_name, 0) > 1:
                    relative_path = key
                    if self.prefix and key.startswith(self.prefix):
                        relative_path = key[len(self.prefix):]
                    semantic_id = relative_path.replace('/', ' / ') if relative_path else file_name
                else:
                    semantic_id = file_name

                batch.append(
                    Document(
                        id=f"{self.bucket_type}:{self.bucket_name}:{key}",
                        blob=blob,
                        source=DocumentSource(self.bucket_type.value),
                        semantic_identifier=semantic_id,
                        extension=get_file_ext(file_name),
                        doc_updated_at=last_modified,
                        size_bytes=size_bytes if size_bytes else 0
                    )
                )
                if len(batch) == self.batch_size:
                    yield batch
                    batch = []

            except Exception:
                logging.exception(f"Error decoding object {key}")

        if batch:
            yield batch