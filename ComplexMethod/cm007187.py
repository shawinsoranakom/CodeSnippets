def _handle_table_field(
        self,
        field_name: str,
        val: Any,
        params: dict[str, Any],
        load_from_db_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Handle table field type with load_from_db column support."""
        if load_from_db_fields is None:
            load_from_db_fields = []
        if val is None:
            params[field_name] = []
            return params

        # Store the table data as-is for now
        # The actual column processing will happen in the loading phase
        if isinstance(val, list) and all(isinstance(item, dict) for item in val):
            params[field_name] = val
        else:
            msg = f"Invalid value type {type(val)} for table field {field_name}"
            raise ValueError(msg)

        # Get table schema from the field to identify load_from_db columns
        field_template = self.template_dict.get(field_name, {})
        table_schema = field_template.get("table_schema", [])

        # Track which columns need database loading
        load_from_db_columns = []
        for column_schema in table_schema:
            if isinstance(column_schema, dict) and column_schema.get("load_from_db"):
                load_from_db_columns.append(column_schema["name"])
            elif hasattr(column_schema, "load_from_db") and column_schema.load_from_db:
                load_from_db_columns.append(column_schema.name)

        # Store metadata for later processing
        if load_from_db_columns:
            # Store table column metadata for the loading phase
            table_load_metadata_key = f"{field_name}_load_from_db_columns"
            params[table_load_metadata_key] = load_from_db_columns

            # Add to load_from_db_fields so it gets processed
            # We'll use a special naming convention to identify table fields
            load_from_db_fields.append(f"table:{field_name}")
            self.load_from_db_fields.append(f"table:{field_name}")

        return params