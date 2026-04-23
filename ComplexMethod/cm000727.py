async def normalize_records(
    records: list[dict],
    table_schema: dict,
    include_field_metadata: bool = False,
) -> dict:
    """
    Normalize Airtable records to include all fields with proper empty values.

    Args:
        records: List of record objects from Airtable API
        table_schema: Table schema containing field definitions
        include_field_metadata: Whether to include field metadata in response

    Returns:
        Dict with normalized records and optionally field metadata
    """
    fields = table_schema.get("fields", [])

    # Normalize each record
    normalized_records = []
    for record in records:
        normalized = {
            "id": record.get("id"),
            "createdTime": record.get("createdTime"),
            "fields": {},
        }

        # Add existing fields
        existing_fields = record.get("fields", {})

        # Add all fields from schema, using empty values for missing ones
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]

            if field_name in existing_fields:
                # Field exists, use its value
                normalized["fields"][field_name] = existing_fields[field_name]
            else:
                # Field is missing, add appropriate empty value
                normalized["fields"][field_name] = get_empty_value_for_field(field_type)

        normalized_records.append(normalized)

    # Build result dictionary
    if include_field_metadata:
        field_metadata = {}
        for field in fields:
            metadata = {"type": field["type"], "id": field["id"]}

            # Add type-specific metadata
            options = field.get("options", {})
            if field["type"] == "currency" and "symbol" in options:
                metadata["symbol"] = options["symbol"]
                metadata["precision"] = options.get("precision", 2)
            elif field["type"] == "duration" and "durationFormat" in options:
                metadata["format"] = options["durationFormat"]
            elif field["type"] == "percent" and "precision" in options:
                metadata["precision"] = options["precision"]
            elif (
                field["type"] in ["singleSelect", "multipleSelects"]
                and "choices" in options
            ):
                metadata["choices"] = [choice["name"] for choice in options["choices"]]
            elif field["type"] == "rating" and "max" in options:
                metadata["max"] = options["max"]
                metadata["icon"] = options.get("icon", "star")
                metadata["color"] = options.get("color", "yellowBright")

            field_metadata[field["name"]] = metadata

        return {"records": normalized_records, "field_metadata": field_metadata}
    else:
        return {"records": normalized_records}