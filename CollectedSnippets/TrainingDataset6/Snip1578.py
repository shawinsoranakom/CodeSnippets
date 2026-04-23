def asdict(field_info: FieldInfo) -> dict[str, Any]:
    attributes = {}
    for attr in _Attrs:
        value = getattr(field_info, attr, Undefined)
        if value is not Undefined:
            attributes[attr] = value
    return {
        "annotation": field_info.annotation,
        "metadata": field_info.metadata,
        "attributes": attributes,
    }