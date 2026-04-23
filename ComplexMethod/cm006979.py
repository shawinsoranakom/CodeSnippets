async def update_tool_list(self, mcp_server_value=None):
        # Accepts mcp_server_value as dict {name, config} or uses self.mcp_server
        mcp_server = mcp_server_value if mcp_server_value is not None else getattr(self, "mcp_server", None)
        server_name = None
        server_config_from_value = None
        if isinstance(mcp_server, dict):
            server_name = mcp_server.get("name")
            server_config_from_value = mcp_server.get("config")
        else:
            server_name = mcp_server
        if not server_name:
            self.tools = []
            return [], {"name": server_name, "config": server_config_from_value}

        # Check if caching is enabled, default to False
        use_cache = getattr(self, "use_cache", False)

        # Use shared cache if available and caching is enabled
        cached = None
        if use_cache:
            servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
            cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None

        if cached is not None:
            try:
                self.tools = cached["tools"]
                self.tool_names = cached["tool_names"]
                self._tool_cache = cached["tool_cache"]
                server_config_from_value = cached["config"]
            except (TypeError, KeyError, AttributeError) as e:
                # Handle corrupted cache data by clearing it and continuing to fetch fresh tools
                msg = f"Unable to use cached data for MCP Server{server_name}: {e}"
                await logger.awarning(msg)
                # Clear the corrupted cache entry
                current_servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                if isinstance(current_servers_cache, dict) and server_name in current_servers_cache:
                    current_servers_cache.pop(server_name)
                    safe_cache_set(self._shared_component_cache, "servers", current_servers_cache)
            else:
                return self.tools, {"name": server_name, "config": server_config_from_value}

        try:
            # Try to fetch from database first to ensure we have the latest config
            # This ensures database updates (like editing a server) take effect
            try:
                from langflow.api.v2.mcp import get_server
                from langflow.services.database.models.user.crud import get_user_by_id

                from lfx.services.deps import get_settings_service
            except ImportError as e:
                msg = (
                    "Langflow MCP server functionality is not available. "
                    "This feature requires the full Langflow installation."
                )
                raise ImportError(msg) from e

            server_config_from_db = None
            async with session_scope() as db:
                if not self.user_id:
                    msg = "User ID is required for fetching MCP tools."
                    raise ValueError(msg)
                current_user = await get_user_by_id(db, self.user_id)

                # Try to get server config from DB/API
                server_config_from_db = await get_server(
                    server_name,
                    current_user,
                    db,
                    storage_service=get_storage_service(),
                    settings_service=get_settings_service(),
                )

            # Resolve config with proper precedence: DB takes priority, falls back to value
            server_config = resolve_mcp_config(
                server_name=server_name,
                server_config_from_value=server_config_from_value,
                server_config_from_db=server_config_from_db,
            )

            if not server_config:
                self.tools = []
                return [], {"name": server_name, "config": server_config}

            # Add verify_ssl option to server config if not present
            if "verify_ssl" not in server_config:
                verify_ssl = getattr(self, "verify_ssl", True)
                server_config["verify_ssl"] = verify_ssl

            # Merge headers from component input with server config headers
            # Component headers take precedence over server config headers
            component_headers = getattr(self, "headers", None) or []
            if component_headers:
                # Convert list of {"key": k, "value": v} to dict
                component_headers_dict = {}
                if isinstance(component_headers, list):
                    for item in component_headers:
                        if isinstance(item, dict) and "key" in item and "value" in item:
                            component_headers_dict[item["key"]] = item["value"]
                elif isinstance(component_headers, dict):
                    component_headers_dict = component_headers

                if component_headers_dict:
                    existing_headers = server_config.get("headers", {}) or {}
                    # Ensure existing_headers is a dict (convert from list if needed)
                    if isinstance(existing_headers, list):
                        existing_dict = {}
                        for item in existing_headers:
                            if isinstance(item, dict) and "key" in item and "value" in item:
                                existing_dict[item["key"]] = item["value"]
                        existing_headers = existing_dict
                    merged_headers = {**existing_headers, **component_headers_dict}
                    server_config["headers"] = merged_headers
            # Get request_variables from graph context for global variable resolution
            request_variables = None
            if hasattr(self, "graph") and self.graph and hasattr(self.graph, "context"):
                request_variables = self.graph.context.get("request_variables")

            # Only load global variables from database if we have headers that might use them
            # This avoids unnecessary database queries when headers are empty
            has_headers = server_config.get("headers") and len(server_config.get("headers", {})) > 0
            if not request_variables and has_headers:
                try:
                    from lfx.services.deps import get_variable_service

                    variable_service = get_variable_service()
                    if variable_service:
                        async with session_scope() as db:
                            request_variables = await variable_service.get_all_decrypted_variables(
                                user_id=self.user_id, session=db
                            )
                except Exception as e:  # noqa: BLE001
                    await logger.awarning(f"Failed to load global variables for MCP component: {e}")

            _, tool_list, tool_cache = await update_tools(
                server_name=server_name,
                server_config=server_config,
                mcp_stdio_client=self.stdio_client,
                mcp_streamable_http_client=self.streamable_http_client,
                request_variables=request_variables,
            )

            self.tool_names = [tool.name for tool in tool_list if hasattr(tool, "name")]
            self._tool_cache = tool_cache
            self.tools = tool_list

            # Cache the result only if caching is enabled
            if use_cache:
                cache_data = {
                    "tools": tool_list,
                    "tool_names": self.tool_names,
                    "tool_cache": tool_cache,
                    "config": server_config,
                }

                # Safely update the servers cache
                current_servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                if isinstance(current_servers_cache, dict):
                    current_servers_cache[server_name] = cache_data
                    safe_cache_set(self._shared_component_cache, "servers", current_servers_cache)

        except (TimeoutError, asyncio.TimeoutError) as e:
            msg = f"Timeout updating tool list: {e!s}"
            await logger.aexception(msg)
            raise TimeoutError(msg) from e
        except Exception as e:
            msg = f"Error updating tool list: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
        else:
            return tool_list, {"name": server_name, "config": server_config}