def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if field_name == "api_key" or (self.api_key and not build_config["tool_name"]["options"]):
            if field_name == "api_key" and not field_value:
                build_config["tool_name"]["options"] = []
                build_config["tool_name"]["value"] = ""

                # Reset the list of actions
                build_config["actions"]["show"] = False
                build_config["actions"]["options"] = []
                build_config["actions"]["value"] = ""

                return build_config

            # Build the list of available tools
            build_config["tool_name"]["options"] = [
                {
                    "name": app.title(),
                    "icon": app,
                    "link": (
                        build_config["tool_name"]["options"][ind]["link"]
                        if build_config["tool_name"]["options"]
                        else ""
                    ),
                }
                for ind, app in enumerate(enabled_tools)
            ]

            return build_config

        if field_name == "tool_name" and field_value:
            composio = self._build_wrapper()

            current_tool_name = (
                field_value
                if isinstance(field_value, str)
                else field_value.get("validate")
                if isinstance(field_value, dict) and "validate" in field_value
                else getattr(self, "tool_name", None)
            )

            if not current_tool_name:
                self.log("No tool name available for connection check")
                return build_config

            try:
                toolkit_slug = current_tool_name.lower()

                connection_list = composio.connected_accounts.list(
                    user_ids=[self.entity_id], toolkit_slugs=[toolkit_slug]
                )

                # Check for active connections
                has_active_connections = False
                if (
                    connection_list
                    and hasattr(connection_list, "items")
                    and connection_list.items
                    and isinstance(connection_list.items, list)
                    and len(connection_list.items) > 0
                ):
                    for connection in connection_list.items:
                        if getattr(connection, "status", None) == "ACTIVE":
                            has_active_connections = True
                            break

                # Get the index of the selected tool in the list of options
                selected_tool_index = next(
                    (
                        ind
                        for ind, tool in enumerate(build_config["tool_name"]["options"])
                        if tool["name"] == current_tool_name.title()
                    ),
                    None,
                )

                if has_active_connections:
                    # User has active connection
                    if selected_tool_index is not None:
                        build_config["tool_name"]["options"][selected_tool_index]["link"] = "validated"

                    # If it's a validation request, validate the tool
                    if (isinstance(field_value, dict) and "validate" in field_value) or isinstance(field_value, str):
                        return self.validate_tool(build_config, field_value, current_tool_name)
                else:
                    # No active connection - create OAuth connection
                    try:
                        connection = composio.toolkits.authorize(user_id=self.entity_id, toolkit=toolkit_slug)
                        redirect_url = getattr(connection, "redirect_url", None)

                        if redirect_url and redirect_url.startswith(("http://", "https://")):
                            if selected_tool_index is not None:
                                build_config["tool_name"]["options"][selected_tool_index]["link"] = redirect_url
                        elif selected_tool_index is not None:
                            build_config["tool_name"]["options"][selected_tool_index]["link"] = "error"
                    except (ValueError, ConnectionError, AttributeError) as e:
                        self.log(f"Error creating OAuth connection: {e}")
                        if selected_tool_index is not None:
                            build_config["tool_name"]["options"][selected_tool_index]["link"] = "error"

            except (ValueError, ConnectionError, AttributeError) as e:
                self.log(f"Error checking connection status: {e}")

        return build_config