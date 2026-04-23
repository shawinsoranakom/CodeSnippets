def _match_lifecycle_filter(
    filter_key: str,
    filter_value: str | int | dict[str, str],
    object_key: ObjectKey,
    size: ObjectSize,
    object_tags: dict[str, str],
):
    match filter_key:
        case "Prefix":
            return object_key.startswith(filter_value)
        case "Tag":
            return object_tags and object_tags.get(filter_value.get("Key")) == filter_value.get(
                "Value"
            )
        case "ObjectSizeGreaterThan":
            return size > filter_value
        case "ObjectSizeLessThan":
            return size < filter_value
        case "Tags":  # this is inside the `And` field
            return object_tags and all(
                object_tags.get(tag.get("Key")) == tag.get("Value") for tag in filter_value
            )