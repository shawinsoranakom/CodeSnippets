def _get_schema_required_entries(
        self,
        schema: dict[str, Any] | None,
        mode: str,
        section_kind: str,
    ) -> list[dict[str, Any]]:
        if not schema:
            return []
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
            req = section.get("required", []) or []
            # Normalize dict-like entries
            return [entry for entry in req if isinstance(entry, dict)]
        return []