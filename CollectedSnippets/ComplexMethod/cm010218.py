def _diff_schema(dst, src):
    additions = {key: src[key] for key in src.keys() - dst.keys()}
    subtractions = {key: dst[key] for key in dst.keys() - src.keys()}

    common_keys = src.keys() & dst.keys()

    versions = {"SCHEMA_VERSION", "TREESPEC_VERSION"}
    common_keys -= versions

    for key in common_keys:
        src_kind = src[key]["kind"]
        src_fields = src[key]["fields"]
        dst_kind = dst[key]["kind"]
        dst_fields = dst[key]["fields"]
        _check(
            src_kind == dst_kind,
            f"Type {key} changed kind from {dst_kind} to {src_kind}",
        )
        if not isinstance(src_fields, dict) or not isinstance(dst_fields, dict):
            raise AssertionError(
                f"expected dict fields, got src={type(src_fields)}, dst={type(dst_fields)}"
            )
        added_fields = {
            key: src_fields[key] for key in src_fields.keys() - dst_fields.keys()
        }
        subtracted_fields = {
            key: dst_fields[key] for key in dst_fields.keys() - src_fields.keys()
        }
        common_fields = src_fields.keys() & dst_fields.keys()

        for field in common_fields:
            src_field = src_fields[field]
            dst_field = dst_fields[field]
            if src_kind == "struct":
                _check(
                    src_field["type"] == dst_field["type"],
                    f"Type of the field {key}.{field} changed from {dst_field['type']} to {src_field['type']}",
                )
                if "default" in src_field and "default" not in dst_field:
                    added_fields[field] = {}
                    added_fields[field]["default"] = src_field["default"]
                if "default" not in src_field and "default" in dst_field:
                    subtracted_fields[field] = {}
                    subtracted_fields[field]["default"] = dst_field["default"]
            elif src_kind == "enum":
                _check(
                    src_field == dst_field,
                    f"Value of the enum field {key}.{field} changed from {dst_field} to {src_field}",
                )
            elif src_kind == "union":
                _check(
                    src_field["type"] == dst_field["type"],
                    f"Type of the field {key}.{field} changed from {dst_field['type']} to {src_field['type']}",
                )
            else:
                raise AssertionError(f"Unknown kind {src_kind}: {key}")
        if len(added_fields) > 0:
            if key in additions:
                raise AssertionError(f"key {key} already in additions")
            additions[key] = {}
            additions[key]["fields"] = added_fields
        if len(subtracted_fields) > 0:
            if key in subtractions:
                raise AssertionError(f"key {key} already in subtractions")
            subtractions[key] = {}
            subtractions[key]["fields"] = subtracted_fields

    return additions, subtractions