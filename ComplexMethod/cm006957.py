def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        """Update the build config based on the selected mode."""
        if field_name != "mode":
            if field_name == "curl_input" and self.mode == "cURL" and self.curl_input:
                return self.parse_curl(self.curl_input, build_config)
            return build_config

        if field_value == "cURL":
            set_field_display(build_config, "curl_input", value=True)
            if build_config["curl_input"]["value"]:
                try:
                    build_config = self.parse_curl(build_config["curl_input"]["value"], build_config)
                except ValueError as e:
                    self.log(f"Failed to parse cURL input: {e}")
        else:
            set_field_display(build_config, "curl_input", value=False)

        return set_current_fields(
            build_config=build_config,
            action_fields=MODE_FIELDS,
            selected_action=field_value,
            default_fields=DEFAULT_FIELDS,
            func=set_field_advanced,
            default_value=True,
        )