def create_combined_model(
    model_name: str,
    *field_sets: dict[str, tuple[Any, Field]],  # type: ignore
    filter_by_provider: str | None = None,
) -> type[BaseModel]:
    """Create a combined pydantic model."""
    combined_fields = {}
    for fields in field_sets:
        for name, (type_annotation, field) in fields.items():
            if (
                filter_by_provider is None
                or "openbb" in field.title  # type: ignore
                or (filter_by_provider in field.title)  # type: ignore
            ):
                combined_fields[name] = (type_annotation, field)

    model = create_model(model_name, **combined_fields)  # type: ignore

    # # Clean up the metadata
    for field in model.model_fields.values():
        if hasattr(field, "metadata"):
            field.metadata = None  # type: ignore

    return model