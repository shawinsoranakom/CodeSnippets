def construct_schema_and_data_format(
    format: str,
    *,
    schema: type[Schema] | None = None,
    with_metadata: bool = False,
    autogenerate_key: bool = False,
    csv_settings: CsvParserSettings | None = None,
    json_field_paths: dict[str, str] | None = None,
    schema_registry_settings: SchemaRegistrySettings | None = None,
    with_native_record_key: bool = False,
    _stacklevel: int = 1,
) -> tuple[type[Schema], api.DataFormat]:
    data_format_type = get_data_format_type(format, SUPPORTED_INPUT_FORMATS)

    if data_format_type == "identity":
        kwargs = locals()
        unexpected_params = [
            "schema",
            "csv_settings",
            "json_field_paths",
        ]
        for param in unexpected_params:
            if param in kwargs and kwargs[param] is not None:
                raise ValueError(f"Unexpected argument for plaintext format: {param}")

        parse_utf8 = format not in ("binary", "only_metadata")
        schema = construct_raw_data_schema_by_flags(
            with_native_record_key=with_native_record_key,
            parse_utf8=parse_utf8,
            with_metadata=with_metadata,
        )
        schema, api_schema = read_schema(schema)

        return schema, api.DataFormat(
            format_type=data_format_type,
            **api_schema,
            parse_utf8=parse_utf8,
            key_generation_policy=(
                api.KeyGenerationPolicy.ALWAYS_AUTOGENERATE
                if autogenerate_key
                else api.KeyGenerationPolicy.PREFER_MESSAGE_KEY
            ),
            schema_registry_settings=maybe_schema_registry_settings(
                schema_registry_settings
            ),
            message_queue_key_field=(
                MESSAGE_QUEUE_KEY_COLUMN_NAME if with_native_record_key else None
            ),
        )

    schema = assert_schema_not_none(schema, data_format_type)
    if with_metadata:
        schema |= MetadataSchema

    schema, api_schema = read_schema(schema)
    if data_format_type == "dsv":
        if json_field_paths is not None:
            raise ValueError("Unexpected argument for csv format: json_field_paths")
        return schema, api.DataFormat(
            **api_schema,
            format_type=data_format_type,
            delimiter=",",
            schema_registry_settings=maybe_schema_registry_settings(
                schema_registry_settings
            ),
        )
    elif data_format_type == "jsonlines":
        if csv_settings is not None:
            raise ValueError("Unexpected argument for json format: csv_settings")
        return schema, api.DataFormat(
            **api_schema,
            format_type=data_format_type,
            column_paths=json_field_paths,
            schema_registry_settings=maybe_schema_registry_settings(
                schema_registry_settings
            ),
        )
    else:
        raise ValueError(f"data format `{format}` not supported")