def _add_text_field(
        self,
        build_config: dict,
        name: str,
        display_name: str,
        info: str | None,
        *,
        required: bool,
        default_value: str | None = None,
    ) -> None:
        """Update existing field or add new text input for custom auth forms."""
        # Check if field already exists in build_config (pre-defined placeholder)
        if name in build_config:
            # Update existing field properties
            build_config[name]["display_name"] = display_name or name.replace("_", " ").title()
            build_config[name]["info"] = info or ""
            build_config[name]["required"] = required
            build_config[name]["show"] = True
            if default_value is not None and default_value != "":
                build_config[name]["value"] = default_value
        else:
            # Create new field if it doesn't exist
            # Use SecretStrInput for sensitive fields
            sensitive_fields = {
                "client_id",
                "client_secret",
                "api_key",
                "api_key_field",
                "generic_api_key",
                "token",
                "access_token",
                "refresh_token",
                "password",
                "bearer_token",
                "authorization_code",
            }

            if name in sensitive_fields:
                field = SecretStrInput(
                    name=name,
                    display_name=display_name or name.replace("_", " ").title(),
                    info=info or "",
                    required=required,
                    real_time_refresh=True,
                    show=True,
                ).to_dict()
            else:
                field = StrInput(
                    name=name,
                    display_name=display_name or name.replace("_", " ").title(),
                    info=info or "",
                    required=required,
                    real_time_refresh=True,
                    show=True,
                ).to_dict()

            if default_value is not None and default_value != "":
                field["value"] = default_value

            # Insert the field in the correct position (before action_button)
            self._insert_field_before_action_button(build_config, name, field)

        self._auth_dynamic_fields.add(name)
        # Also add to class-level cache for better tracking
        self.__class__.get_all_auth_field_names().add(name)