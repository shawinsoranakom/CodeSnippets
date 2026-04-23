def construct(
        cls,
        table: Table,
        *,
        format: str = "json",
        delimiter: str = ",",
        key: ColumnReference | None = None,
        value: ColumnReference | None = None,
        headers: Iterable[ColumnReference] | None = None,
        topic_name: ColumnReference | None = None,
        schema_registry_settings: SchemaRegistrySettings | None = None,
        subject: str | None = None,
        allowed_key_types: tuple[dt.DType, ...] | None = (dt.BYTES, dt.STR, dt.ANY),
        allowed_value_types: tuple[dt.DType, ...] | None = (dt.BYTES, dt.STR, dt.ANY),
    ) -> MessageQueueOutputFormat:
        key_field_index = None
        header_fields: dict[str, int] = {}
        extracted_field_indices: dict[str, int] = {}
        columns_to_extract: list[ColumnReference] = []

        if topic_name is not None:
            topic_name_index = cls.add_column_reference_to_extract(
                topic_name, columns_to_extract, extracted_field_indices
            )
            if topic_name._column.dtype not in (dt.STR, dt.ANY):
                raise ValueError(
                    "The topic name column must have a string type, however "
                    f"{topic_name._column.dtype.typehint} is used"
                )
        else:
            topic_name_index = None

        # Common part for all formats: obtain key field index and prepare header fields
        if key is not None:
            if (
                allowed_key_types is not None
                and table[key._name]._column.dtype not in allowed_key_types
            ):
                raise ValueError(
                    f"The key column must have one of the following types: {allowed_key_types}"
                )
            key_field_index = cls.add_column_reference_to_extract(
                key, columns_to_extract, extracted_field_indices
            )
        if headers is not None:
            for header in headers:
                header_fields[header.name] = cls.add_column_reference_to_extract(
                    header, columns_to_extract, extracted_field_indices
                )

        # Format-dependent parts: handle json and dsv separately
        if format == "json" or format == "dsv":
            if value is not None:
                raise ValueError(
                    f"'value' and format='{format}' cannot be set at the same time"
                )
            for column_name in table._columns:
                cls.add_column_reference_to_extract(
                    table[column_name], columns_to_extract, extracted_field_indices
                )
            table = table.select(*columns_to_extract)
            data_format = api.DataFormat(
                format_type="jsonlines" if format == "json" else "dsv",
                key_field_names=[],
                value_fields=_format_output_value_fields(table),
                delimiter=delimiter,
                schema_registry_settings=maybe_schema_registry_settings(
                    schema_registry_settings
                ),
                subject=subject,
            )
        elif format == "raw" or format == "plaintext":
            value_field_index = None
            if key is not None and value is None:
                raise ValueError("'value' must be specified if 'key' is not None")
            if value is not None:
                value_field_index = cls.add_column_reference_to_extract(
                    value, columns_to_extract, extracted_field_indices
                )
            else:
                column_names = list(table._columns.keys())
                if len(column_names) != 1:
                    raise ValueError(
                        f"'{format}' format without explicit 'value' specification "
                        "can only be used with single-column tables"
                    )
                value = table[column_names[0]]
                value_field_index = cls.add_column_reference_to_extract(
                    value, columns_to_extract, extracted_field_indices
                )

            table = table.select(*columns_to_extract)
            if (
                allowed_value_types is not None
                and table[value._name]._column.dtype not in allowed_value_types
            ):
                raise ValueError(
                    f"The value column must have one of the following types: {allowed_value_types}"
                )

            data_format = api.DataFormat(
                format_type="single_column",
                key_field_names=[],
                value_fields=_format_output_value_fields(table),
                value_field_index=value_field_index,
                schema_registry_settings=maybe_schema_registry_settings(
                    schema_registry_settings
                ),
                subject=subject,
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

        return cls(
            table=table,
            key_field_index=key_field_index,
            header_fields=header_fields,
            data_format=data_format,
            topic_name_index=topic_name_index,
        )