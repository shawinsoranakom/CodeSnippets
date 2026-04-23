def _hide_all_action_fields(self, build_config: dict) -> None:
        """Hide and reset all action parameter inputs, regardless of trace flags."""
        # Hide known action fields
        for fname in list(self._all_fields):
            if fname in build_config and isinstance(build_config[fname], dict):
                build_config[fname]["show"] = False
                build_config[fname]["value"] = "" if fname not in self._bool_variables else False
        # Hide any other visible, non-protected fields that look like parameters
        protected = {
            # Component control fields
            "entity_id",
            "api_key",
            "auth_link",
            "action_button",
            "tool_mode",
            "auth_mode",
            "auth_mode_pill",
            "create_auth_config",
            # Pre-defined auth fields
            "client_id",
            "client_secret",
            "verification_token",
            "redirect_uri",
            "authorization_url",
            "token_url",
            "api_key_field",
            "generic_api_key",
            "token",
            "access_token",
            "refresh_token",
            "username",
            "password",
            "domain",
            "base_url",
            "bearer_token",
            "authorization_code",
            "scopes",
            "subdomain",
            "instance_url",
            "tenant_id",
        }
        # Add all reserved Component attributes to protected set
        protected.update(self.RESERVED_ATTRIBUTES)
        # Also add the renamed versions (with app_name prefix) to protected set
        for attr in self.RESERVED_ATTRIBUTES:
            protected.add(f"{self.app_name}_{attr}")
        # Add all dynamic auth fields to protected set
        protected.update(self._auth_dynamic_fields)
        # Also protect any auth fields discovered across all instances
        protected.update(self.__class__.get_all_auth_field_names())

        for key, cfg in list(build_config.items()):
            if key in protected:
                continue
            if isinstance(cfg, dict) and "show" in cfg:
                cfg["show"] = False
                if "value" in cfg:
                    cfg["value"] = ""