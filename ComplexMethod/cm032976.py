def _yield_webdav_documents(
        self,
        start: datetime,
        end: datetime,
    ) -> GenerateDocumentsOutput:
        """Generate documents from WebDAV server

        Args:
            start: Start datetime for filtering
            end: End datetime for filtering

        Yields:
            Batches of documents
        """
        if self.client is None:
            raise ConnectorMissingCredentialError("WebDAV client not initialized")

        logging.info(f"Searching for files in {self.remote_path} between {start} and {end}")
        files = self._list_files_recursive(self.remote_path, start, end)
        logging.info(f"Found {len(files)} files matching time criteria")

        filename_counts: dict[str, int] = {}
        for file_path, _ in files:
            file_name = os.path.basename(file_path)
            filename_counts[file_name] = filename_counts.get(file_name, 0) + 1

        batch: list[Document] = []
        for file_path, file_info in files:
            file_name = os.path.basename(file_path)

            if not self._is_supported_file(file_name):
                logging.debug(f"Skipping file {file_path} due to unsupported extension.")
                continue

            size_bytes = file_info.get('size', 0)
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
                logging.debug(f"Downloading file: {file_path}")
                from io import BytesIO
                buffer = BytesIO()
                self.client.download_fileobj(file_path, buffer)
                blob = buffer.getvalue()

                if blob is None or len(blob) == 0:
                    logging.warning(f"Downloaded content is empty for {file_path}")
                    continue

                modified_time = file_info.get('modified')
                if modified_time:
                    if isinstance(modified_time, datetime):
                        modified = modified_time
                        if modified.tzinfo is None:
                            modified = modified.replace(tzinfo=timezone.utc)
                    elif isinstance(modified_time, str):
                        try:
                            modified = datetime.strptime(modified_time, '%a, %d %b %Y %H:%M:%S %Z')
                            modified = modified.replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            try:
                                modified = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                            except (ValueError, TypeError):
                                logging.warning(f"Could not parse modified time for {file_path}: {modified_time}")
                                modified = datetime.now(timezone.utc)
                    else:
                        modified = datetime.now(timezone.utc)
                else:
                    modified = datetime.now(timezone.utc)

                if filename_counts.get(file_name, 0) > 1:
                    relative_path = file_path
                    if file_path.startswith(self.remote_path):
                        relative_path = file_path[len(self.remote_path):]
                    if relative_path.startswith('/'):
                        relative_path = relative_path[1:]
                    semantic_id = relative_path.replace('/', ' / ') if relative_path else file_name
                else:
                    semantic_id = file_name

                batch.append(
                    Document(
                        id=f"webdav:{self.base_url}:{file_path}",
                        blob=blob,
                        source=DocumentSource.WEBDAV,
                        semantic_identifier=semantic_id,
                        extension=get_file_ext(file_name),
                        doc_updated_at=modified,
                        size_bytes=size_bytes if size_bytes else 0
                    )
                )

                if len(batch) == self.batch_size:
                    yield batch
                    batch = []

            except Exception as e:
                logging.exception(f"Error downloading file {file_path}: {e}")

        if batch:
            yield batch