def convert_document(self, es_doc: dict[str, Any]) -> dict[str, Any]:
        """
        Convert an ES document to OceanBase row format.

        Args:
            es_doc: Elasticsearch document (with _id and _source)

        Returns:
            Dictionary ready for OceanBase insertion
        """
        # Extract _id and _source
        doc_id = es_doc.get("_id")
        source = es_doc.get("_source", es_doc)

        row = {}

        # Set document ID
        if doc_id:
            row["id"] = str(doc_id)
        elif "id" in source:
            row["id"] = str(source["id"])

        # Process each field
        for field_name, field_def in RAGFLOW_COLUMNS.items():
            if field_name == "id":
                continue  # Already handled

            value = source.get(field_name)

            if value is None:
                # Use default if available
                default = field_def.get("default")
                if default is not None:
                    row[field_name] = default
                continue

            # Convert based on field type
            row[field_name] = self._convert_field_value(
                field_name, value, field_def
            )

        # Handle vector fields
        for key, value in source.items():
            if VECTOR_FIELD_PATTERN.match(key):
                if isinstance(value, list):
                    row[key] = value
                self.vector_fields.add(key)

        # Handle unknown fields -> store in 'extra'
        extra_fields = {}
        for key, value in source.items():
            if key not in RAGFLOW_COLUMNS and not VECTOR_FIELD_PATTERN.match(key):
                extra_fields[key] = value

        if extra_fields:
            existing_extra = row.get("extra")
            if existing_extra and isinstance(existing_extra, dict):
                existing_extra.update(extra_fields)
            else:
                row["extra"] = json.dumps(extra_fields, ensure_ascii=False)

        return row