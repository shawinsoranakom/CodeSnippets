async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:

        data = await list_records(
            credentials,
            input_data.base_id,
            input_data.table_id_or_name,
            filter_by_formula=(
                input_data.filter_formula if input_data.filter_formula else None
            ),
            view=input_data.view if input_data.view else None,
            sort=input_data.sort if input_data.sort else None,
            max_records=input_data.max_records if input_data.max_records else None,
            page_size=min(input_data.page_size, 100) if input_data.page_size else None,
            offset=input_data.offset if input_data.offset else None,
            fields=input_data.return_fields if input_data.return_fields else None,
        )

        records = data.get("records", [])

        # Normalize output if requested
        if input_data.normalize_output:
            # Fetch table schema
            table_schema = await get_table_schema(
                credentials, input_data.base_id, input_data.table_id_or_name
            )

            # Normalize the records
            normalized_data = await normalize_records(
                records,
                table_schema,
                include_field_metadata=input_data.include_field_metadata,
            )

            yield "records", normalized_data["records"]
            yield "offset", data.get("offset", None)

            if (
                input_data.include_field_metadata
                and "field_metadata" in normalized_data
            ):
                yield "field_metadata", normalized_data["field_metadata"]
        else:
            yield "records", records
            yield "offset", data.get("offset", None)