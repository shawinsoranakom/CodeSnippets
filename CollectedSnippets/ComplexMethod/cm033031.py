def _row_to_document(self, row: Union[tuple, list, Dict[str, Any]], column_names: list) -> Document:
        """Convert a database row to a Document."""
        row_dict = dict(zip(column_names, row)) if isinstance(row, (list, tuple)) else row

        content_parts = []
        for col in self.content_columns:
            if col in row_dict and row_dict[col] is not None:
                value = row_dict[col]
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                # Use brackets around field name and put value on a new line
                # so that TxtParser preserves field boundaries after chunking.
                content_parts.append(f"【{col}】:\n{value}")

        content = "\n\n".join(content_parts)

        if self.id_column and self.id_column in row_dict:
            doc_id = f"{self.db_type}:{self.database}:{row_dict[self.id_column]}"
        else:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            doc_id = f"{self.db_type}:{self.database}:{content_hash}"

        metadata = {}
        for col in self.metadata_columns:
            if col in row_dict and row_dict[col] is not None:
                value = row_dict[col]
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                else:
                    value = str(value)
                metadata[col] = value

        doc_updated_at = datetime.now(timezone.utc)
        if self.timestamp_column and self.timestamp_column in row_dict:
            ts_value = row_dict[self.timestamp_column]
            if isinstance(ts_value, datetime):
                if ts_value.tzinfo is None:
                    doc_updated_at = ts_value.replace(tzinfo=timezone.utc)
                else:
                    doc_updated_at = ts_value

        first_content_col = self.content_columns[0] if self.content_columns else "record"
        semantic_id = str(row_dict.get(first_content_col, "database_record")).replace("\n", " ").replace("\r", " ").strip()[:100]


        return Document(
            id=doc_id,
            blob=content.encode("utf-8"),
            source=DocumentSource(self.db_type.value),
            semantic_identifier=semantic_id,
            extension=".txt",
            doc_updated_at=doc_updated_at,
            size_bytes=len(content.encode("utf-8")),
            metadata=metadata if metadata else None,
        )