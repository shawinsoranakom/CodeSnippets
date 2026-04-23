def mime_type_matches_binary_media_types(mime_type: str | None, binary_media_types: list[str]):
    if not mime_type or not binary_media_types:
        return False

    mime_type_and_subtype = mime_type.split(",")[0].split(";")[0].split("/")
    if len(mime_type_and_subtype) != 2:
        return False
    mime_type, mime_subtype = mime_type_and_subtype

    for bmt in binary_media_types:
        type_and_subtype = bmt.split(";")[0].split("/")
        if len(type_and_subtype) != 2:
            continue
        _type, subtype = type_and_subtype
        if _type == "*":
            continue

        if subtype == "*" and mime_type == _type:
            return True

        if mime_type == _type and mime_subtype == subtype:
            return True

    return False