def _render_auth_mode_dropdown(self, build_config: dict, modes: list[str]) -> None:
        """Populate and show the auth_mode control; if only one mode, show as selected chip-style list."""
        try:
            build_config.setdefault("auth_mode", {})
            auth_mode_cfg = build_config["auth_mode"]
            # Prefer the connected scheme if known; otherwise use schema-provided modes as-is
            stored_scheme = (build_config.get("auth_link") or {}).get("auth_scheme")
            if isinstance(stored_scheme, str) and stored_scheme:
                modes = [stored_scheme]

            if len(modes) <= 1:
                # Single mode → show a pill in the auth_mode slot (right after API Key)
                selected = modes[0] if modes else ""
                try:
                    pill = TabInput(
                        name="auth_mode",
                        display_name="Auth Mode",
                        options=[selected] if selected else [],
                        value=selected,
                    ).to_dict()
                    pill["show"] = True
                    build_config["auth_mode"] = pill
                except (TypeError, ValueError, AttributeError):
                    build_config["auth_mode"] = {
                        "name": "auth_mode",
                        "display_name": "Auth Mode",
                        "type": "tab",
                        "options": [selected],
                        "value": selected,
                        "show": True,
                    }
            else:
                # Multiple modes → normal dropdown, hide the display chip if present
                auth_mode_cfg["options"] = modes
                auth_mode_cfg["show"] = True
                if not auth_mode_cfg.get("value") and modes:
                    auth_mode_cfg["value"] = modes[0]
                if "auth_mode_display" in build_config:
                    build_config["auth_mode_display"]["show"] = False
            auth_mode_cfg["helper_text"] = "Choose how to authenticate with the toolkit."
        except (TypeError, ValueError, AttributeError) as e:
            logger.debug(f"Failed to render auth_mode dropdown: {e}")