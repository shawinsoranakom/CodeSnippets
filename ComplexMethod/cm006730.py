def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        """Update build config for auth and action selection."""
        # Avoid normalizing legacy input_types here; rely on upstream fixes

        # BULLETPROOF tool_mode checking - check all possible places where tool_mode could be stored
        instance_tool_mode = getattr(self, "tool_mode", False) if hasattr(self, "tool_mode") else False

        # Check build_config for tool_mode in multiple possible structures
        build_config_tool_mode = False
        if "tool_mode" in build_config:
            tool_mode_config = build_config["tool_mode"]
            if isinstance(tool_mode_config, dict):
                build_config_tool_mode = tool_mode_config.get("value", False)
            else:
                build_config_tool_mode = bool(tool_mode_config)

        # If this is a tool_mode change, update BOTH instance variable AND build_config
        if field_name == "tool_mode":
            self.tool_mode = field_value
            instance_tool_mode = field_value
            # CRITICAL: Store tool_mode state in build_config so it persists
            if "tool_mode" not in build_config:
                build_config["tool_mode"] = {}
            if isinstance(build_config["tool_mode"], dict):
                build_config["tool_mode"]["value"] = field_value
            build_config_tool_mode = field_value

        # Current tool_mode is True if ANY source indicates it's enabled
        current_tool_mode = instance_tool_mode or build_config_tool_mode or (field_name == "tool_mode" and field_value)

        # CRITICAL: Ensure dynamic action metadata is available whenever we have an API key
        # This must happen BEFORE any early returns to ensure tools are always loaded
        api_key_available = hasattr(self, "api_key") and self.api_key

        # Check if we need to populate actions - but also check cache availability
        actions_available = bool(self._actions_data)
        toolkit_slug = getattr(self, "app_name", "").lower()
        cached_actions_available = toolkit_slug in self.__class__.get_actions_cache()

        should_populate = False

        if (field_name == "api_key" and field_value) or (
            api_key_available and not actions_available and not cached_actions_available
        ):
            should_populate = True
        elif api_key_available and not actions_available and cached_actions_available:
            self._populate_actions_data()

        if should_populate:
            logger.info(f"Populating actions data for {getattr(self, 'app_name', 'unknown')}...")
            self._populate_actions_data()
            logger.info(f"Actions populated: {len(self._actions_data)} actions found")
            # Also fetch toolkit schema to drive auth UI
            schema = self._get_toolkit_schema()
            modes = self._extract_auth_modes_from_schema(schema)
            self._render_auth_mode_dropdown(build_config, modes)
            # If a mode is selected (including auto-default), render custom fields when not managed
            try:
                selected_mode = (build_config.get("auth_mode") or {}).get("value")
                managed = (schema or {}).get("composio_managed_auth_schemes") or []
                # Don't render custom fields if "Composio_Managed" is selected
                # For API_KEY and other token modes, no fields are needed as they use link method
                token_modes = ["API_KEY", "BEARER_TOKEN", "BASIC"]
                if selected_mode and selected_mode not in ["Composio_Managed", *token_modes]:
                    self._clear_auth_dynamic_fields(build_config)
                    self._render_custom_auth_fields(build_config, schema or {}, selected_mode)
                    # Already reordered in _render_custom_auth_fields
                elif selected_mode in token_modes:
                    # Clear any existing auth fields for token-based modes
                    self._clear_auth_dynamic_fields(build_config)
            except (TypeError, ValueError, AttributeError):
                pass

        # CRITICAL: Set action options if we have actions (either from fresh population or cache)
        if self._actions_data:
            self._build_action_maps()
            build_config["action_button"]["options"] = [
                {"name": self.sanitize_action_name(action), "metadata": action} for action in self._actions_data
            ]
            logger.info(f"Action options set in build_config: {len(build_config['action_button']['options'])} options")
            # Always (re)populate auth_mode as well when actions are available
            schema = self._get_toolkit_schema()
            modes = self._extract_auth_modes_from_schema(schema)
            self._render_auth_mode_dropdown(build_config, modes)
        else:
            build_config["action_button"]["options"] = []
            logger.warning("No actions found, setting empty options")

        # clear stored connection_id when api_key is changed
        if field_name == "api_key" and field_value:
            stored_connection_before = build_config.get("auth_link", {}).get("connection_id")
            if "auth_link" in build_config and "connection_id" in build_config["auth_link"]:
                build_config["auth_link"].pop("connection_id", None)
                build_config["auth_link"]["value"] = "connect"
                build_config["auth_link"]["auth_tooltip"] = "Connect"
                logger.info(f"Cleared stored connection_id '{stored_connection_before}' due to API key change")
            else:
                logger.info("DEBUG: EARLY No stored connection_id to clear on API key change")
            # Also clear any stored scheme and reset auth mode UI when API key changes
            build_config.setdefault("auth_link", {})
            build_config["auth_link"].pop("auth_scheme", None)
            build_config.setdefault("auth_mode", {})
            build_config["auth_mode"].pop("value", None)
            build_config["auth_mode"]["show"] = True
            # If auth_mode is currently a TabInput pill, convert it back to dropdown
            if isinstance(build_config.get("auth_mode"), dict) and build_config["auth_mode"].get("type") == "tab":
                build_config["auth_mode"].pop("type", None)
            # Re-render dropdown options for the new API key context
            try:
                schema = self._get_toolkit_schema()
                modes = self._extract_auth_modes_from_schema(schema)
                # Rebuild as DropdownInput to ensure proper rendering
                dd = DropdownInput(
                    name="auth_mode",
                    display_name="Auth Mode",
                    options=modes,
                    placeholder="Select auth mode",
                    toggle=True,
                    toggle_disable=True,
                    show=True,
                    real_time_refresh=True,
                    helper_text="Choose how to authenticate with the toolkit.",
                ).to_dict()
                build_config["auth_mode"] = dd
            except (TypeError, ValueError, AttributeError):
                pass
            # NEW: Clear any selected action and hide generated fields when API key is re-entered
            try:
                if "action_button" in build_config and isinstance(build_config["action_button"], dict):
                    build_config["action_button"]["value"] = "disabled"
                self._hide_all_action_fields(build_config)
            except (TypeError, ValueError, AttributeError):
                pass

        # Handle disconnect operations when tool mode is enabled
        if field_name == "auth_link" and field_value == "disconnect":
            # Soft disconnect: do not delete remote account; only clear local state
            stored_connection_id = build_config.get("auth_link", {}).get("connection_id")
            if not stored_connection_id:
                logger.warning("No connection ID found to disconnect (soft)")
            build_config.setdefault("auth_link", {})
            build_config["auth_link"]["value"] = "connect"
            build_config["auth_link"]["auth_tooltip"] = "Connect"
            build_config["auth_link"].pop("connection_id", None)
            build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
            build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}
            return self.update_input_types(build_config)

        # Handle auth mode change -> render appropriate fields based on schema
        if field_name == "auth_mode":
            schema = self._get_toolkit_schema() or {}
            # Clear any previously rendered auth fields when switching modes
            self._clear_auth_fields_from_schema(build_config, schema)
            mode = field_value if isinstance(field_value, str) else (build_config.get("auth_mode", {}).get("value"))
            if not mode and isinstance(build_config.get("auth_mode"), dict):
                mode = build_config["auth_mode"].get("value")
            # Always show auth_link for any mode
            build_config.setdefault("auth_link", {})
            build_config["auth_link"]["show"] = False
            # Reset connection state when switching modes
            build_config["auth_link"].pop("connection_id", None)
            build_config["auth_link"].pop("auth_config_id", None)
            build_config["auth_link"]["value"] = "connect"
            build_config["auth_link"]["auth_tooltip"] = "Connect"
            # If an ACTIVE connection already exists, don't render any auth fields
            existing_active = self._find_active_connection_for_app(self.app_name)
            if existing_active:
                connection_id, _ = existing_active
                self._clear_auth_fields_from_schema(build_config, schema)
                build_config.setdefault("create_auth_config", {})
                build_config["create_auth_config"]["show"] = False
                build_config["auth_link"]["value"] = "validated"
                build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                build_config["auth_link"]["connection_id"] = connection_id
                # Reflect the connected auth scheme in the UI
                scheme, _ = self._get_connection_auth_info(connection_id)
                if scheme:
                    build_config.setdefault("auth_link", {})
                    build_config["auth_link"]["auth_scheme"] = scheme
                    build_config.setdefault("auth_mode", {})
                    build_config["auth_mode"]["value"] = scheme
                    build_config["auth_mode"]["options"] = [scheme]
                    build_config["auth_mode"]["show"] = False
                    try:
                        pill = TabInput(
                            name="auth_mode",
                            display_name="Auth Mode",
                            options=[scheme],
                            value=scheme,
                        ).to_dict()
                        pill["show"] = True
                        build_config["auth_mode"] = pill
                    except (TypeError, ValueError, AttributeError):
                        build_config["auth_mode"] = {
                            "name": "auth_mode",
                            "display_name": "Auth Mode",
                            "type": "tab",
                            "options": [scheme],
                            "value": scheme,
                            "show": True,
                        }
                    build_config["action_button"]["helper_text"] = ""
                    build_config["action_button"]["helper_text_metadata"] = {}
                    return self.update_input_types(build_config)
            if mode:
                managed = schema.get("composio_managed_auth_schemes") or []
                # Always hide the Create Auth Config control (used internally only)
                build_config.setdefault("create_auth_config", {})
                build_config["create_auth_config"]["show"] = False
                build_config["create_auth_config"]["display_name"] = ""
                build_config["create_auth_config"]["value"] = ""
                build_config["create_auth_config"]["helper_text"] = ""
                build_config["create_auth_config"]["options"] = ["create"]
                if mode == "Composio_Managed":
                    # Composio_Managed → no extra fields needed
                    pass
                elif mode in ["API_KEY", "BEARER_TOKEN", "BASIC"]:
                    # Token-based modes → no fields needed, user enters on Composio page via link
                    pass
                elif isinstance(managed, list) and mode in managed:
                    # This is a specific managed auth scheme (e.g., OAUTH2) but user can still choose custom
                    # So we should render custom fields for this mode
                    self._render_custom_auth_fields(build_config, schema, mode)
                    # Already reordered in _render_custom_auth_fields
                else:
                    # Custom → render only required fields based on the toolkit schema
                    self._render_custom_auth_fields(build_config, schema, mode)
                    # Already reordered in _render_custom_auth_fields
                return self.update_input_types(build_config)

        # Handle connection initiation when tool mode is enabled
        if field_name == "auth_link" and isinstance(field_value, dict):
            try:
                toolkit_slug = self.app_name.lower()

                # First check if we already have an ACTIVE connection
                existing_active = self._find_active_connection_for_app(self.app_name)
                if existing_active:
                    connection_id, _ = existing_active
                    build_config["auth_link"]["value"] = "validated"
                    build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                    build_config["auth_link"]["connection_id"] = connection_id
                    build_config["action_button"]["helper_text"] = ""
                    build_config["action_button"]["helper_text_metadata"] = {}

                    # Clear auth fields when connected
                    schema = self._get_toolkit_schema()
                    self._clear_auth_fields_from_schema(build_config, schema)

                    # Convert auth_mode to pill for connected state
                    scheme, _ = self._get_connection_auth_info(connection_id)
                    if scheme:
                        build_config.setdefault("auth_mode", {})
                        build_config["auth_mode"]["value"] = scheme
                        build_config["auth_mode"]["options"] = [scheme]
                        build_config["auth_mode"]["show"] = False
                        try:
                            pill = TabInput(
                                name="auth_mode",
                                display_name="Auth Mode",
                                options=[scheme],
                                value=scheme,
                            ).to_dict()
                            pill["show"] = True
                            build_config["auth_mode"] = pill
                        except (TypeError, ValueError, AttributeError):
                            build_config["auth_mode"] = {
                                "name": "auth_mode",
                                "display_name": "Auth Mode",
                                "type": "tab",
                                "options": [scheme],
                                "value": scheme,
                                "show": True,
                            }

                    logger.info(f"Using existing ACTIVE connection {connection_id} for {toolkit_slug}")
                    return self.update_input_types(build_config)

                # Only reuse ACTIVE connections; otherwise create a new connection
                stored_connection_id = None

                # Create new connection ONLY if we truly have no usable connection yet
                if existing_active is None:
                    # Check if we already have a redirect URL in progress
                    current_auth_link_value = build_config.get("auth_link", {}).get("value", "")
                    if current_auth_link_value and current_auth_link_value.startswith(("http://", "https://")):
                        # We already have a redirect URL, don't create a new one
                        logger.info(f"Redirect URL already exists for {toolkit_slug}, skipping new creation")
                        return self.update_input_types(build_config)

                    try:
                        # Determine auth mode
                        schema = self._get_toolkit_schema()
                        mode = None
                        if isinstance(build_config.get("auth_mode"), dict):
                            mode = build_config["auth_mode"].get("value")
                        # If no managed default exists (400 Default auth config), require mode selection
                        managed = (schema or {}).get("composio_managed_auth_schemes") or []

                        # Handle "Composio_Managed" mode explicitly
                        if mode == "Composio_Managed":
                            # Use Composio_Managed auth flow
                            redirect_url, connection_id = self._initiate_connection(toolkit_slug)
                            build_config["auth_link"]["value"] = redirect_url
                            logger.info(f"New OAuth URL created for {toolkit_slug}: {redirect_url}")
                            return self.update_input_types(build_config)

                        if not mode:
                            build_config["auth_link"]["value"] = "connect"
                            build_config["auth_link"]["auth_tooltip"] = "Select Auth Mode"
                            return self.update_input_types(build_config)
                        # Custom modes: create auth config and/or initiate with config
                        # Only validate auth_config_creation fields for OAUTH2
                        required_missing = []
                        if mode == "OAUTH2":
                            req_names_pre = self._get_schema_field_names(
                                schema,
                                "OAUTH2",
                                "auth_config_creation",
                                "required",
                            )
                            for fname in req_names_pre:
                                if fname in build_config:
                                    val = build_config[fname].get("value")
                                    if val in (None, ""):
                                        required_missing.append(fname)
                        if required_missing:
                            # Surface errors on each missing field
                            for fname in required_missing:
                                if fname in build_config and isinstance(build_config[fname], dict):
                                    build_config[fname]["helper_text"] = "This field is required"
                                    build_config[fname]["helper_text_metadata"] = {"variant": "destructive"}
                                    # Also reflect in info for guaranteed visibility
                                    existing_info = build_config[fname].get("info") or ""
                                    build_config[fname]["info"] = f"Required: {existing_info}".strip()
                                    build_config[fname]["show"] = True
                            # Add a visible top-level hint near Auth Mode as well
                            build_config.setdefault("auth_mode", {})
                            missing_joined = ", ".join(required_missing)
                            build_config["auth_mode"]["helper_text"] = f"Missing required: {missing_joined}"
                            build_config["auth_mode"]["helper_text_metadata"] = {"variant": "destructive"}
                            build_config["auth_link"]["value"] = "connect"
                            build_config["auth_link"]["auth_tooltip"] = f"Missing: {missing_joined}"
                            return self.update_input_types(build_config)
                        composio = self._build_wrapper()
                        if mode == "OAUTH2":
                            # If an auth_config was already created via the button, use it and include initiation fields
                            stored_ac_id = (build_config.get("auth_link") or {}).get("auth_config_id")
                            if stored_ac_id:
                                # Check if we already have a redirect URL to prevent duplicates
                                current_link_value = build_config.get("auth_link", {}).get("value", "")
                                if current_link_value and current_link_value.startswith(("http://", "https://")):
                                    logger.info(
                                        f"Redirect URL already exists for {toolkit_slug} OAUTH2, skipping new creation"
                                    )
                                    return self.update_input_types(build_config)

                                # Use link method - no need to collect connection initiation fields
                                redirect = composio.connected_accounts.link(
                                    user_id=self.entity_id,
                                    auth_config_id=stored_ac_id,
                                )
                                redirect_url = getattr(redirect, "redirect_url", None)
                                connection_id = getattr(redirect, "id", None)
                                if redirect_url:
                                    build_config["auth_link"]["value"] = redirect_url
                                if connection_id:
                                    build_config["auth_link"]["connection_id"] = connection_id
                                # Clear action blocker text on successful initiation
                                build_config["action_button"]["helper_text"] = ""
                                build_config["action_button"]["helper_text_metadata"] = {}
                                # Clear any auth fields
                                schema = self._get_toolkit_schema()
                                self._clear_auth_fields_from_schema(build_config, schema)
                                return self.update_input_types(build_config)
                            # Otherwise, create custom OAuth2 auth config using schema-declared required fields
                            credentials = {}
                            missing = []
                            # Collect required names from schema
                            req_names = self._get_schema_field_names(
                                schema,
                                "OAUTH2",
                                "auth_config_creation",
                                "required",
                            )
                            candidate_names = set(self._auth_dynamic_fields) | req_names
                            for fname in candidate_names:
                                if fname in build_config:
                                    val = build_config[fname].get("value")
                                    if val not in (None, ""):
                                        credentials[fname] = val
                                    else:
                                        missing.append(fname)
                            # proceed even if missing optional; backend will validate
                            # Check if we already have a redirect URL to prevent duplicates
                            current_link_value = build_config.get("auth_link", {}).get("value", "")
                            if current_link_value and current_link_value.startswith(("http://", "https://")):
                                logger.info(
                                    f"Redirect URL already exists for {toolkit_slug} OAUTH2, skipping new creation"
                                )
                                return self.update_input_types(build_config)

                            ac = composio.auth_configs.create(
                                toolkit=toolkit_slug,
                                options={
                                    "type": "use_custom_auth",
                                    "auth_scheme": "OAUTH2",
                                    "credentials": credentials,
                                },
                            )
                            auth_config_id = getattr(ac, "id", None)
                            # Use link method directly - no need to check for connection initiation fields
                            redirect = composio.connected_accounts.link(
                                user_id=self.entity_id,
                                auth_config_id=auth_config_id,
                            )
                            redirect_url = getattr(redirect, "redirect_url", None)
                            connection_id = getattr(redirect, "id", None)
                            if redirect_url:
                                build_config["auth_link"]["value"] = redirect_url
                            if connection_id:
                                build_config["auth_link"]["connection_id"] = connection_id
                            # Hide auth fields immediately after successful initiation
                            schema = self._get_toolkit_schema()
                            self._clear_auth_fields_from_schema(build_config, schema)
                            build_config["action_button"]["helper_text"] = ""
                            build_config["action_button"]["helper_text_metadata"] = {}
                            return self.update_input_types(build_config)
                        if mode == "API_KEY":
                            # Check if we already have a redirect URL to prevent duplicates
                            current_link_value = build_config.get("auth_link", {}).get("value", "")
                            if current_link_value and current_link_value.startswith(("http://", "https://")):
                                logger.info(
                                    f"Redirect URL already exists for {toolkit_slug} API_KEY, skipping new creation"
                                )
                                return self.update_input_types(build_config)

                            ac = composio.auth_configs.create(
                                toolkit=toolkit_slug,
                                options={"type": "use_custom_auth", "auth_scheme": "API_KEY", "credentials": {}},
                            )
                            auth_config_id = getattr(ac, "id", None)
                            # Use link method - user will enter API key on Composio page
                            initiation = composio.connected_accounts.link(
                                user_id=self.entity_id,
                                auth_config_id=auth_config_id,
                            )
                            connection_id = getattr(initiation, "id", None)
                            redirect_url = getattr(initiation, "redirect_url", None)
                            # API_KEY now also returns redirect URL with new link method
                            if redirect_url:
                                build_config["auth_link"]["value"] = redirect_url
                                build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                            # Hide auth fields immediately after successful initiation
                            schema = self._get_toolkit_schema()
                            self._clear_auth_fields_from_schema(build_config, schema)
                            build_config["action_button"]["helper_text"] = ""
                            build_config["action_button"]["helper_text_metadata"] = {}

                            return self.update_input_types(build_config)
                        # Generic custom auth flow for any other mode (treat like API_KEY)
                        # Check if we already have a redirect URL to prevent duplicates
                        current_link_value = build_config.get("auth_link", {}).get("value", "")
                        if current_link_value and current_link_value.startswith(("http://", "https://")):
                            logger.info(f"Redirect URL already exists for {toolkit_slug} {mode}, skipping new creation")
                            return self.update_input_types(build_config)

                        ac = composio.auth_configs.create(
                            toolkit=toolkit_slug,
                            options={"type": "use_custom_auth", "auth_scheme": mode, "credentials": {}},
                        )
                        auth_config_id = getattr(ac, "id", None)
                        # Use link method - user will enter required fields on Composio page
                        initiation = composio.connected_accounts.link(
                            user_id=self.entity_id,
                            auth_config_id=auth_config_id,
                        )
                        connection_id = getattr(initiation, "id", None)
                        redirect_url = getattr(initiation, "redirect_url", None)
                        if redirect_url:
                            build_config["auth_link"]["value"] = redirect_url
                            build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                        # Clear auth fields
                        schema = self._get_toolkit_schema()
                        self._clear_auth_fields_from_schema(build_config, schema)
                        build_config["action_button"]["helper_text"] = ""
                        build_config["action_button"]["helper_text_metadata"] = {}
                        return self.update_input_types(build_config)
                    except (ValueError, ConnectionError, TypeError) as e:
                        logger.error(f"Error creating connection: {e}")
                        build_config["auth_link"]["value"] = "connect"
                        build_config["auth_link"]["auth_tooltip"] = f"Error: {e!s}"
                    else:
                        return self.update_input_types(build_config)
                else:
                    # We already have a usable connection; no new OAuth request
                    build_config["auth_link"]["auth_tooltip"] = "Disconnect"

            except (ValueError, ConnectionError) as e:
                logger.error(f"Error in connection initiation: {e}")
                build_config["auth_link"]["value"] = "connect"
                build_config["auth_link"]["auth_tooltip"] = f"Error: {e!s}"
                build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
                build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}
                return build_config

        # Check for ACTIVE connections and update status accordingly (tool mode)
        if hasattr(self, "api_key") and self.api_key:
            stored_connection_id = build_config.get("auth_link", {}).get("connection_id")
            active_connection_id = None

            # First try to check stored connection ID
            if stored_connection_id:
                status = self._check_connection_status_by_id(stored_connection_id)
                if status == "ACTIVE":
                    active_connection_id = stored_connection_id

            # If no stored connection or stored connection is not ACTIVE, find any ACTIVE connection
            if not active_connection_id:
                active_connection = self._find_active_connection_for_app(self.app_name)
                if active_connection:
                    active_connection_id, _ = active_connection
                    # Store the found active connection ID for future use
                    if "auth_link" not in build_config:
                        build_config["auth_link"] = {}
                    build_config["auth_link"]["connection_id"] = active_connection_id

            if active_connection_id:
                # Show validated connection status
                build_config["auth_link"]["value"] = "validated"
                build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                build_config["auth_link"]["show"] = False
                # Update auth mode UI to reflect connected scheme
                scheme, _ = self._get_connection_auth_info(active_connection_id)
                if scheme:
                    build_config.setdefault("auth_link", {})
                    build_config["auth_link"]["auth_scheme"] = scheme
                    build_config.setdefault("auth_mode", {})
                    build_config["auth_mode"]["value"] = scheme
                    build_config["auth_mode"]["options"] = [scheme]
                    build_config["auth_mode"]["show"] = False
                    try:
                        pill = TabInput(
                            name="auth_mode",
                            display_name="Auth Mode",
                            options=[scheme],
                            value=scheme,
                        ).to_dict()
                        pill["show"] = True
                        build_config["auth_mode"] = pill
                    except (TypeError, ValueError, AttributeError):
                        build_config["auth_mode"] = {
                            "name": "auth_mode",
                            "display_name": "Auth Mode",
                            "type": "tab",
                            "options": [scheme],
                            "value": scheme,
                            "show": True,
                        }
                    build_config["action_button"]["helper_text"] = ""
                    build_config["action_button"]["helper_text_metadata"] = {}
                # Clear any auth fields since we are already connected
                schema = self._get_toolkit_schema()
                self._clear_auth_fields_from_schema(build_config, schema)
                build_config.setdefault("create_auth_config", {})
                build_config["create_auth_config"]["show"] = False
                build_config["action_button"]["helper_text"] = ""
                build_config["action_button"]["helper_text_metadata"] = {}
            else:
                build_config["auth_link"]["value"] = "connect"
                build_config["auth_link"]["auth_tooltip"] = "Connect"
                build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
                build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}

        # CRITICAL: If tool_mode is enabled from ANY source, hide action UI but keep auth flow available
        if current_tool_mode:
            build_config["action_button"]["show"] = False

            # Hide ALL action parameter fields when tool mode is enabled
            for field in self._all_fields:
                if field in build_config:
                    build_config[field]["show"] = False

            # Also hide any other action-related fields that might be in build_config
            for field_name_in_config in build_config:  # noqa: PLC0206
                # Skip base fields like api_key, tool_mode, action, etc., and dynamic auth fields
                if (
                    field_name_in_config
                    not in [
                        "api_key",
                        "tool_mode",
                        "action_button",
                        "auth_link",
                        "entity_id",
                        "auth_mode",
                        "auth_mode_pill",
                    ]
                    and field_name_in_config not in getattr(self, "_auth_dynamic_fields", set())
                    and isinstance(build_config[field_name_in_config], dict)
                    and "show" in build_config[field_name_in_config]
                ):
                    build_config[field_name_in_config]["show"] = False

            # ENSURE tool_mode state is preserved in build_config for future calls
            if "tool_mode" not in build_config:
                build_config["tool_mode"] = {"value": True}
            elif isinstance(build_config["tool_mode"], dict):
                build_config["tool_mode"]["value"] = True
            # Keep auth UI available and render fields if needed
            build_config.setdefault("auth_link", {})
            build_config["auth_link"]["show"] = False
            build_config["auth_link"]["display_name"] = ""

            # Only render auth fields if NOT already connected
            active_connection = self._find_active_connection_for_app(self.app_name)
            if not active_connection:
                try:
                    schema = self._get_toolkit_schema()
                    mode = (build_config.get("auth_mode") or {}).get("value")
                    managed = (schema or {}).get("composio_managed_auth_schemes") or []
                    token_modes = ["API_KEY", "BEARER_TOKEN", "BASIC"]
                    if (
                        mode
                        and mode not in ["Composio_Managed", *token_modes]
                        and not getattr(self, "_auth_dynamic_fields", set())
                    ):
                        self._render_custom_auth_fields(build_config, schema or {}, mode)
                        # Already reordered in _render_custom_auth_fields
                except (TypeError, ValueError, AttributeError):
                    pass
            else:
                # If connected, clear any auth fields that might be showing
                self._clear_auth_dynamic_fields(build_config)
            # Do NOT return here; allow auth flow to run in Tool Mode

        if field_name == "tool_mode":
            if field_value is True:
                build_config["action_button"]["show"] = False  # Hide action field when tool mode is enabled
                for field in self._all_fields:
                    build_config[field]["show"] = False  # Update show status for all fields based on tool mode
            elif field_value is False:
                build_config["action_button"]["show"] = True  # Show action field when tool mode is disabled
                for field in self._all_fields:
                    build_config[field]["show"] = True  # Update show status for all fields based on tool mode
            return self.update_input_types(build_config)

        if field_name == "action_button":
            # If selection is cancelled/cleared, remove generated fields
            def _is_cleared(val: Any) -> bool:
                return (
                    not val
                    or (
                        isinstance(val, list)
                        and (len(val) == 0 or (len(val) > 0 and isinstance(val[0], dict) and not val[0].get("name")))
                    )
                    or (isinstance(val, str) and val in ("", "disabled", "placeholder"))
                )

            if _is_cleared(field_value):
                self._hide_all_action_fields(build_config)
                return self.update_input_types(build_config)

            self._update_action_config(build_config, field_value)
            # Keep the existing show/hide behaviour
            self.show_hide_fields(build_config, field_value)
            return self.update_input_types(build_config)

        # Handle auth config button click
        if field_name == "create_auth_config" and field_value == "create":
            try:
                # Check if we already have a redirect URL to prevent duplicates
                current_link_value = build_config.get("auth_link", {}).get("value", "")
                if current_link_value and current_link_value.startswith(("http://", "https://")):
                    logger.info("Redirect URL already exists, skipping new auth config creation")
                    return self.update_input_types(build_config)

                composio = self._build_wrapper()
                toolkit_slug = self.app_name.lower()
                schema = self._get_toolkit_schema() or {}
                # Collect required fields from the current build_config
                credentials = {}
                req_names = self._get_schema_field_names(schema, "OAUTH2", "auth_config_creation", "required")
                candidate_names = set(self._auth_dynamic_fields) | req_names
                for fname in candidate_names:
                    if fname in build_config:
                        val = build_config[fname].get("value")
                        if val not in (None, ""):
                            credentials[fname] = val
                # Create a new auth config using the collected credentials
                ac = composio.auth_configs.create(
                    toolkit=toolkit_slug,
                    options={"type": "use_custom_auth", "auth_scheme": "OAUTH2", "credentials": credentials},
                )
                auth_config_id = getattr(ac, "id", None)
                build_config.setdefault("auth_link", {})
                if auth_config_id:
                    # Use link method directly - no need to check for connection initiation fields
                    connection_request = composio.connected_accounts.link(
                        user_id=self.entity_id, auth_config_id=auth_config_id
                    )
                    redirect_url = getattr(connection_request, "redirect_url", None)
                    connection_id = getattr(connection_request, "id", None)
                    if redirect_url and redirect_url.startswith(("http://", "https://")):
                        build_config["auth_link"]["value"] = redirect_url
                        build_config["auth_link"]["auth_tooltip"] = "Disconnect"
                        build_config["auth_link"]["connection_id"] = connection_id
                        build_config["action_button"]["helper_text"] = ""
                        build_config["action_button"]["helper_text_metadata"] = {}
                        logger.info(f"New OAuth URL created for {toolkit_slug}: {redirect_url}")
                    else:
                        logger.error(f"Failed to initiate connection with new auth config: {redirect_url}")
                        build_config["auth_link"]["value"] = "error"
                        build_config["auth_link"]["auth_tooltip"] = f"Error: {redirect_url}"
                else:
                    logger.error(f"Failed to create new auth config for {toolkit_slug}")
                    build_config["auth_link"]["value"] = "error"
                    build_config["auth_link"]["auth_tooltip"] = "Create Auth Config failed"
            except (ValueError, ConnectionError, TypeError) as e:
                logger.error(f"Error creating new auth config: {e}")
                build_config["auth_link"]["value"] = "error"
                build_config["auth_link"]["auth_tooltip"] = f"Error: {e!s}"
            return self.update_input_types(build_config)

        # Handle API key removal
        if field_name == "api_key" and len(field_value) == 0:
            build_config["auth_link"]["value"] = ""
            build_config["auth_link"]["auth_tooltip"] = "Please provide a valid Composio API Key."
            build_config["action_button"]["options"] = []
            build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
            build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}
            build_config.setdefault("auth_link", {})
            build_config["auth_link"].pop("connection_id", None)
            build_config["auth_link"].pop("auth_scheme", None)
            # Restore auth_mode dropdown and hide pill
            try:
                dd = DropdownInput(
                    name="auth_mode",
                    display_name="Auth Mode",
                    options=[],
                    placeholder="Select auth mode",
                    toggle=True,
                    toggle_disable=True,
                    show=True,
                    real_time_refresh=True,
                    helper_text="Choose how to authenticate with the toolkit.",
                ).to_dict()
                build_config["auth_mode"] = dd
            except (TypeError, ValueError, AttributeError):
                build_config.setdefault("auth_mode", {})
                build_config["auth_mode"]["show"] = True
                build_config["auth_mode"].pop("value", None)
            # NEW: Clear any selected action and hide generated fields when API key is cleared
            try:
                if "action_button" in build_config and isinstance(build_config["action_button"], dict):
                    build_config["action_button"]["value"] = "disabled"
                self._hide_all_action_fields(build_config)
            except (TypeError, ValueError, AttributeError):
                pass
            return self.update_input_types(build_config)

        # Only proceed with connection logic if we have an API key
        if not hasattr(self, "api_key") or not self.api_key:
            return self.update_input_types(build_config)

        # CRITICAL: If tool_mode is enabled (check both instance and build_config), skip all connection logic
        if current_tool_mode:
            build_config["action_button"]["show"] = False
            return self.update_input_types(build_config)

        # Update action options only if tool_mode is disabled
        self._build_action_maps()
        # Only set options if they haven't been set already during action population
        if "options" not in build_config.get("action_button", {}) or not build_config["action_button"]["options"]:
            build_config["action_button"]["options"] = [
                {"name": self.sanitize_action_name(action), "metadata": action} for action in self._actions_data
            ]
            logger.debug("Setting action options from main logic path")
        else:
            logger.debug("Action options already set, skipping duplicate setting")
        # Only set show=True if tool_mode is not enabled
        if not current_tool_mode:
            build_config["action_button"]["show"] = True

        stored_connection_id = build_config.get("auth_link", {}).get("connection_id")
        active_connection_id = None

        if stored_connection_id:
            status = self._check_connection_status_by_id(stored_connection_id)
            if status == "ACTIVE":
                active_connection_id = stored_connection_id

        if not active_connection_id:
            active_connection = self._find_active_connection_for_app(self.app_name)
            if active_connection:
                active_connection_id, _ = active_connection
                if "auth_link" not in build_config:
                    build_config["auth_link"] = {}
                build_config["auth_link"]["connection_id"] = active_connection_id

        if active_connection_id:
            build_config["auth_link"]["value"] = "validated"
            build_config["auth_link"]["auth_tooltip"] = "Disconnect"
            build_config["action_button"]["helper_text"] = ""
            build_config["action_button"]["helper_text_metadata"] = {}

            # Clear auth fields when connected
            schema = self._get_toolkit_schema()
            self._clear_auth_fields_from_schema(build_config, schema)

            # Convert auth_mode to pill for connected state
            scheme, _ = self._get_connection_auth_info(active_connection_id)
            if scheme:
                build_config.setdefault("auth_mode", {})
                build_config["auth_mode"]["value"] = scheme
                build_config["auth_mode"]["options"] = [scheme]
                build_config["auth_mode"]["show"] = False
                try:
                    pill = TabInput(
                        name="auth_mode",
                        display_name="Auth Mode",
                        options=[scheme],
                        value=scheme,
                    ).to_dict()
                    pill["show"] = True
                    build_config["auth_mode"] = pill
                except (TypeError, ValueError, AttributeError):
                    build_config["auth_mode"] = {
                        "name": "auth_mode",
                        "display_name": "Auth Mode",
                        "type": "tab",
                        "options": [scheme],
                        "value": scheme,
                        "show": True,
                    }
        elif stored_connection_id:
            status = self._check_connection_status_by_id(stored_connection_id)
            if status == "INITIATED":
                current_value = build_config.get("auth_link", {}).get("value")
                if not current_value or current_value == "connect":
                    build_config["auth_link"]["value"] = "connect"
                build_config["auth_link"]["auth_tooltip"] = "Connect"
                build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
                build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}
            else:
                # Connection not found or other status
                build_config["auth_link"]["value"] = "connect"
                build_config["auth_link"]["auth_tooltip"] = "Connect"
                build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
                build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}
        else:
            build_config["auth_link"]["value"] = "connect"
            build_config["auth_link"]["auth_tooltip"] = "Connect"
            build_config["action_button"]["helper_text"] = "Please connect before selecting actions."
            build_config["action_button"]["helper_text_metadata"] = {"variant": "destructive"}

        if self._is_tool_mode_enabled():
            build_config["action_button"]["show"] = False

        return self.update_input_types(build_config)