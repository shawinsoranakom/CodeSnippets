def _map_cli_args_to_settings(server_kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Map command line arguments to MCPSettings field names.

        This handles the translation between CLI argument names and settings field names,
        and separates out Uvicorn and httpx-specific configurations.
        """
        mcp_settings_fields = set(MCPSettings.model_fields.keys())
        cli_to_settings_map = {
            "allowed_categories": "allowed_tool_categories",
            "default_categories": "default_tool_categories",
            "tool_discovery": "enable_tool_discovery",
            "system_prompt": "system_prompt_file",
            "system-prompt": "system_prompt_file",
            "server_prompts": "server_prompts_file",
            "server-prompts": "server_prompts_file",
        }
        uvicorn_fields = {
            "host",
            "port",
            "log_level",
            "debug",
            "uds",
            "fd",
            "workers",
            "loop",
            "http",
            "env_file",
            "log_config",
            "access_log",
            "use_colors",
            "proxy_headers",
            "server_header",
            "date_header",
            "forwarded_allow_ips",
            "ssl_keyfile",
            "ssl_certfile",
            "ssl_keyfile_password",
            "ssl_version",
            "ssl_cert_reqs",
            "ssl_ca_certs",
            "ssl_ciphers",
            "header",
            "version",
        }
        excluded_fields = {"transport"}
        httpx_fields = {k for k in server_kwargs if k.startswith("httpx_")}

        settings_overrides: dict[str, Any] = {}
        uvicorn_config: dict[str, Any] = {}
        httpx_config: dict[str, Any] = {}

        for key, value in server_kwargs.items():
            if key in excluded_fields or value is None:
                continue

            if key in httpx_fields:
                httpx_key = key.replace("httpx_", "", 1)
                httpx_config[httpx_key] = value
            elif key in uvicorn_fields:
                uvicorn_config[key] = value
            elif key in cli_to_settings_map:
                mapped_key = cli_to_settings_map[key]
                settings_overrides[mapped_key] = value
            elif key in mcp_settings_fields:
                settings_overrides[key] = value
            else:
                # Fallback for unknown fields to uvicorn_config
                uvicorn_config[key] = value

        if uvicorn_config:
            settings_overrides.setdefault("uvicorn_config", {}).update(uvicorn_config)
        if httpx_config:
            settings_overrides.setdefault("httpx_client_kwargs", {}).update(
                httpx_config
            )

        return settings_overrides