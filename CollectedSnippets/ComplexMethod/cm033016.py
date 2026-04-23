def load_from_state(self) -> GenerateDocumentsOutput:
        """
        Fetch all Airtable records and ingest attachments as raw blobs.

        Each attachment is converted into a single Document(blob=...).
        """
        if not self._airtable_client:
            raise ConnectorMissingCredentialError("Airtable credentials not loaded")

        table = self.airtable_client.table(self.base_id, self.table_name_or_id)
        records = table.all()

        logging.info(
            f"Starting Airtable blob ingestion for table {self.table_name_or_id}, "
            f"{len(records)} records found."
        )

        batch: list[Document] = []

        for record in records:
            record_id = record.get("id")
            fields = record.get("fields", {})
            created_time = record.get("createdTime")

            for field_value in fields.values():
                # We only care about attachment fields (lists of dicts with url/filename)
                if not isinstance(field_value, list):
                    continue

                for attachment in field_value:
                    url = attachment.get("url")
                    filename = attachment.get("filename")
                    attachment_id = attachment.get("id")

                    if not url or not filename or not attachment_id:
                        continue

                    try:
                        resp = requests.get(url, timeout=30)
                        resp.raise_for_status()
                        content = resp.content
                    except Exception:
                        logging.exception(
                            f"Failed to download attachment {filename} "
                            f"(record={record_id})"
                        )
                        continue
                    size_bytes = extract_size_bytes(attachment)
                    if (
                        self.size_threshold is not None
                        and isinstance(size_bytes, int)
                        and size_bytes > self.size_threshold
                    ):
                        logging.warning(
                            f"{filename} exceeds size threshold of {self.size_threshold}. Skipping."
                        )
                        continue
                    batch.append(
                        Document(
                            id=f"airtable:{record_id}:{attachment_id}",
                            blob=content,
                            source=DocumentSource.AIRTABLE,
                            semantic_identifier=filename,
                            extension=get_file_ext(filename),
                            size_bytes=size_bytes if size_bytes else 0,
                            doc_updated_at=datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                        )
                    )

                    if len(batch) >= self.batch_size:
                        yield batch
                        batch = []

        if batch:
            yield batch