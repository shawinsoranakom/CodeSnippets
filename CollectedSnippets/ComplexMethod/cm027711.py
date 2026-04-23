def check_extraneous_translation_fields(
    integration: Integration,
    service_name: str,
    strings: dict[str, Any],
    service_schema: dict[str, Any],
) -> None:
    """Check for extraneous translation fields."""
    if integration.core and "services" in strings:
        section_fields = set()
        for field in service_schema.get("fields", {}).values():
            if "fields" in field:
                # This is a section
                section_fields.update(field["fields"].keys())
        translation_fields = {
            field
            for field in strings["services"][service_name].get("fields", {})
            if field not in service_schema.get("fields", {})
        }
        for field in translation_fields - section_fields:
            integration.add_error(
                "services",
                f"Service {service_name} has a field {field} in the translations file that is not in the schema",
            )