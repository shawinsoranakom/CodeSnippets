def _collect_all_auth_field_names(self, schema: dict[str, Any] | None) -> set[str]:
        names: set[str] = set()
        if not schema:
            return names
        details = schema.get("auth_config_details") or schema.get("authConfigDetails") or []
        for item in details:
            fields = (item.get("fields") or {}) if isinstance(item, dict) else {}
            for section_key in (
                "auth_config_creation",
                "authConfigCreation",
                "connected_account_initiation",
                "connectedAccountInitiation",
            ):
                section = fields.get(section_key) or {}
                for bucket in ("required", "optional"):
                    for entry in section.get(bucket, []) or []:
                        name = entry.get("name") if isinstance(entry, dict) else None
                        if name:
                            names.add(name)
                            # Add to class-level cache for tracking all discovered auth fields
                            self.__class__.get_all_auth_field_names().add(name)
        # Only use names discovered from the toolkit schema; do not add aliases
        return names