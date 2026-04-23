def _merge_fields(
        current: DataclassField, incoming: DataclassField, query: bool = False
    ) -> DataclassField:
        """Merge 2 dataclass fields."""
        curr_name = current.name
        curr_type: type | None = current.annotation
        curr_desc = getattr(current.default, "description", "")
        curr_json_schema_extra = getattr(current.default, "json_schema_extra", {})

        inc_type: type | None = incoming.annotation
        inc_desc = getattr(incoming.default, "description", "")
        inc_json_schema_extra = getattr(incoming.default, "json_schema_extra", {})

        def split_desc(desc: str) -> str:
            """Split field description, removing provider tags and multiple items text."""
            item = desc.split(" (provider: ")
            detail = item[0] if item else ""
            # Also remove "Multiple comma separated items allowed." for comparison
            detail = detail.replace(" Multiple comma separated items allowed.", "")
            detail = detail.replace("Multiple comma separated items allowed.", "")
            return detail.strip()

        def merge_json_schema_extra(curr: dict, inc: dict) -> dict:
            """Merge json schema extra."""
            for key in curr.keys() & inc.keys():
                # Merge keys that are in both dictionaries if both are lists
                curr_value = curr[key]
                inc_value = inc[key]
                if isinstance(curr_value, list) and isinstance(inc_value, list):
                    curr[key] = list(set(curr.get(key, []) + inc.get(key, [])))
                    inc.pop(key)

            # Add any remaining keys from inc to curr
            curr.update(inc)
            return curr

        json_schema_extra: dict = merge_json_schema_extra(
            curr=curr_json_schema_extra or {}, inc=inc_json_schema_extra or {}
        )

        curr_detail = split_desc(curr_desc)
        inc_detail = split_desc(inc_desc)

        curr_title = getattr(current.default, "title", "") or ""
        inc_title = getattr(incoming.default, "title", "") or ""
        # Filter out empty titles and join
        provider_list = [t for t in [curr_title, inc_title] if t]
        providers = ",".join(provider_list)
        formatted_prov = ", ".join(provider_list)

        if SequenceMatcher(None, curr_detail, inc_detail).ratio() > 0.8:
            new_desc = f"{curr_detail} (provider: {formatted_prov})"
        else:
            new_desc = f"{curr_desc};\n    {inc_desc}"

        QF: Callable = Query if query else FieldInfo  # type: ignore[assignment]
        merged_default = QF(
            default=getattr(current.default, "default", None),
            title=providers,
            description=new_desc,
            json_schema_extra=json_schema_extra,
        )

        merged_type: type | None = (
            Union[curr_type, inc_type] if curr_type != inc_type else curr_type  # type: ignore[assignment]  # noqa
        )

        return DataclassField(curr_name, merged_type, merged_default)