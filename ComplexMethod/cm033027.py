def _yield_documents_from_table(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        """
        Yield documents from all sheets in the table.

        Args:
            start: Optional start timestamp for filtering
            end: Optional end timestamp for filtering

        Yields:
            Lists of Document objects
        """
        # Get all sheets
        sheets = self._get_all_sheets()

        batch: list[Document] = []

        for sheet in sheets:
            sheet_id = sheet["id"]
            sheet_name = sheet["name"]

            # Get all records from this sheet
            records = self._get_all_records(sheet_id)

            for record in records:
                doc = self._convert_record_to_document(
                    record=record,
                    sheet_id=sheet_id,
                    sheet_name=sheet_name,
                )

                # Apply time filtering if specified
                if start is not None or end is not None:
                    doc_time = doc.doc_updated_at.timestamp() if doc.doc_updated_at else None
                    if doc_time is not None:
                        if start is not None and doc_time < start:
                            continue
                        if end is not None and doc_time > end:
                            continue

                batch.append(doc)

                if len(batch) >= self.batch_size:
                    yield batch
                    batch = []

        if batch:
            yield batch