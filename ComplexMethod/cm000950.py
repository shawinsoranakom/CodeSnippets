async def _expand(
        value: Any,
        *,
        prop_schema: dict[str, Any] | None = None,
    ) -> Any:
        """Recursively expand a single argument value.

        Strings are checked for ``@@agptfile:`` references and expanded
        (bare refs get structured parsing; embedded refs get inline
        substitution).  Dicts and lists are traversed recursively,
        threading the corresponding sub-schema from *prop_schema* so
        that nested fields also receive correct type-aware expansion.
        Non-string scalars pass through unchanged.
        """
        if isinstance(value, str):
            ref = parse_file_ref(value)
            if ref is not None:
                # MediaFileType fields: return the raw URI immediately —
                # no file reading, no format inference, no content parsing.
                if _is_media_file_field(prop_schema):
                    return ref.uri

                fmt = infer_format_from_uri(ref.uri)
                # Workspace URIs by ID (workspace://abc123) have no extension.
                # When the MIME fragment is also missing, fall back to the
                # workspace file manager's metadata for format detection.
                if fmt is None and ref.uri.startswith("workspace://"):
                    fmt = await _infer_format_from_workspace(ref.uri, user_id, session)
                return await _expand_bare_ref(ref, fmt, user_id, session, prop_schema)

            # Not a bare ref — do normal inline expansion.
            return await expand_file_refs_in_string(
                value, user_id, session, raise_on_error=True
            )
        if isinstance(value, dict):
            # When the schema says this is an object but doesn't define
            # inner properties, skip expansion — the caller (e.g.
            # RunBlockTool) will expand with the actual nested schema.
            if (
                prop_schema is not None
                and prop_schema.get("type") == "object"
                and "properties" not in prop_schema
            ):
                return value
            nested_props = (prop_schema or {}).get("properties", {})
            return {
                k: await _expand(v, prop_schema=nested_props.get(k))
                for k, v in value.items()
            }
        if isinstance(value, list):
            items_schema = (prop_schema or {}).get("items")
            return [await _expand(item, prop_schema=items_schema) for item in value]
        return value