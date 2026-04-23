def _get_schema_field_names(
        self,
        schema: dict[str, Any] | None,
        mode: str,
        section_kind: str,
        bucket: str,
    ) -> set[str]:
        names: set[str] = set()
        if not schema:
            return names
        details = schema.get("auth_config_details") or schema.get("authConfigDetails") or []
        for item in details:
            if (item.get("mode") or item.get("auth_method")) != mode:
                continue
            fields = item.get("fields") or {}
            section = (
                fields.get(section_kind)
                or fields.get(
                    "authConfigCreation" if section_kind == "auth_config_creation" else "connectedAccountInitiation"
                )
                or {}
            )
            for entry in section.get(bucket, []) or []:
                name = entry.get("name") if isinstance(entry, dict) else None
                if name:
                    names.add(name)
        return names