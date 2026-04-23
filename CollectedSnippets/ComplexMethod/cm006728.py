def _render_custom_auth_fields(self, build_config: dict, schema: dict[str, Any], mode: str) -> None:
        """Render fields for custom auth based on schema auth_config_details sections."""
        details = schema.get("auth_config_details") or schema.get("authConfigDetails") or []
        selected = None
        for item in details:
            if (item.get("mode") or item.get("auth_method")) == mode:
                selected = item
                break
        if not selected:
            return
        fields = selected.get("fields") or {}

        # Helper function to process fields
        def process_fields(field_list: list, *, required: bool) -> None:
            for field in field_list:
                name = field.get("name")
                if not name:
                    continue
                # Skip Access Token field (bearer_token)
                if name == "bearer_token":
                    continue
                # Skip fields with default values for both required and optional fields
                default_val = field.get("default")
                if default_val is not None:
                    continue
                disp = field.get("display_name") or field.get("displayName") or name
                desc = field.get("description")
                self._add_text_field(build_config, name, disp, desc, required=required, default_value=default_val)

        # Only process AuthConfigCreation fields (for custom OAuth2, etc.)
        # Connection initiation fields are now handled on Composio page via link method
        creation = fields.get("auth_config_creation") or fields.get("authConfigCreation") or {}
        # Process required fields
        process_fields(creation.get("required", []), required=True)
        # Process optional fields (excluding those with defaults and bearer_token)
        process_fields(creation.get("optional", []), required=False)