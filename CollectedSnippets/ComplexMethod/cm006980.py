async def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        """Toggle the visibility of connection-specific fields based on the selected mode."""
        try:
            if field_name == "tool":
                try:
                    # Always refresh tools when cache is disabled, or when tools list is empty
                    # This ensures database edits are reflected immediately when cache is disabled
                    use_cache = getattr(self, "use_cache", False)
                    if len(self.tools) == 0 or not use_cache:
                        try:
                            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()
                            build_config["tool"]["options"] = [tool.name for tool in self.tools]
                            build_config["tool"]["placeholder"] = "Select a tool"
                        except (TimeoutError, asyncio.TimeoutError) as e:
                            msg = f"Timeout updating tool list: {e!s}"
                            await logger.aexception(msg)
                            if not build_config["tools_metadata"]["show"]:
                                build_config["tool"]["show"] = True
                                build_config["tool"]["options"] = []
                                build_config["tool"]["value"] = ""
                                build_config["tool"]["placeholder"] = "Timeout on MCP server"
                            else:
                                build_config["tool"]["show"] = False
                        except ValueError:
                            if not build_config["tools_metadata"]["show"]:
                                build_config["tool"]["show"] = True
                                build_config["tool"]["options"] = []
                                build_config["tool"]["value"] = ""
                                build_config["tool"]["placeholder"] = "Error on MCP Server"
                            else:
                                build_config["tool"]["show"] = False

                    if field_value == "":
                        return build_config
                    tool_obj = None
                    for tool in self.tools:
                        if tool.name == field_value:
                            tool_obj = tool
                            break
                    if tool_obj is None:
                        msg = f"Tool {field_value} not found in available tools: {self.tools}"
                        await logger.awarning(msg)
                        return build_config
                    await self._update_tool_config(build_config, field_value)
                except Exception as e:
                    build_config["tool"]["options"] = []
                    msg = f"Failed to update tools: {e!s}"
                    raise ValueError(msg) from e
                else:
                    return build_config
            elif field_name == "mcp_server":
                if not field_value:
                    build_config["tool"]["show"] = False
                    build_config["tool"]["options"] = []
                    build_config["tool"]["value"] = ""
                    build_config["tool"]["placeholder"] = ""
                    build_config["tool_placeholder"]["tool_mode"] = False
                    self.remove_non_default_keys(build_config)
                    return build_config

                build_config["tool_placeholder"]["tool_mode"] = True

                current_server_name = field_value.get("name") if isinstance(field_value, dict) else field_value
                _last_selected_server = safe_cache_get(self._shared_component_cache, "last_selected_server", "")
                # Only treat as a server change if there was a previous server selection.
                # Cold cache (_last_selected_server="") on initial flow load is NOT a server change —
                # the user didn't switch anything, the backend just hasn't seen this component yet.
                server_changed = bool(_last_selected_server and current_server_name != _last_selected_server)

                # Determine if "Tool Mode" is active by checking if the tool dropdown is hidden.
                is_in_tool_mode = build_config["tools_metadata"]["show"]

                # Get use_cache setting to determine if we should use cached data
                use_cache = getattr(self, "use_cache", False)

                # Fast path: if server didn't change and we already have options, keep them as-is
                # BUT only if caching is enabled, we're in tool mode, or it's the initial load
                existing_options = build_config.get("tool", {}).get("options") or []
                if not server_changed and existing_options:
                    # In non-tool mode with cache disabled, skip the fast path to force refresh
                    # BUT on initial load (cold cache), always preserve saved options from the flow
                    if not is_in_tool_mode and not use_cache and _last_selected_server:
                        pass  # Continue to refresh logic below (user-initiated with cache disabled)
                    else:
                        if not is_in_tool_mode:
                            build_config["tool"]["show"] = True
                        safe_cache_set(self._shared_component_cache, "last_selected_server", current_server_name)
                        return build_config

                # To avoid unnecessary updates, only proceed if the server has actually changed
                # OR if caching is disabled (to force refresh in non-tool mode)
                if (_last_selected_server in (current_server_name, "")) and build_config["tool"]["show"] and use_cache:
                    if current_server_name:
                        servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                        if isinstance(servers_cache, dict):
                            cached = servers_cache.get(current_server_name)
                            if cached is not None and cached.get("tool_names"):
                                cached_tools = cached["tool_names"]
                                current_tools = build_config["tool"]["options"]
                                if current_tools == cached_tools:
                                    return build_config
                    else:
                        return build_config
                safe_cache_set(self._shared_component_cache, "last_selected_server", current_server_name)

                # When cache is disabled, clear any cached data for this server
                # This ensures we always fetch fresh data from the database
                if not use_cache and current_server_name:
                    servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                    if isinstance(servers_cache, dict) and current_server_name in servers_cache:
                        servers_cache.pop(current_server_name)
                        safe_cache_set(self._shared_component_cache, "servers", servers_cache)

                # Check if tools are already cached for this server before clearing
                cached_tools = None
                if current_server_name and use_cache:
                    servers_cache = safe_cache_get(self._shared_component_cache, "servers", {})
                    if isinstance(servers_cache, dict):
                        cached = servers_cache.get(current_server_name)
                        if cached is not None:
                            try:
                                cached_tools = cached["tools"]
                                self.tools = cached_tools
                                self.tool_names = cached["tool_names"]
                                self._tool_cache = cached["tool_cache"]
                            except (TypeError, KeyError, AttributeError) as e:
                                # Handle corrupted cache data by ignoring it
                                msg = f"Unable to use cached data for MCP Server,{current_server_name}: {e}"
                                await logger.awarning(msg)
                                cached_tools = None

                # Clear tools when cache is disabled OR when we don't have cached tools
                # This ensures fresh tools are fetched after database edits
                if not cached_tools or not use_cache:
                    self.tools = []  # Clear previous tools to force refresh

                # Clear previous tool inputs if:
                # 1. Server actually changed
                # 2. Cache is disabled (meaning tool list will be refreshed)
                if server_changed or not use_cache:
                    self.remove_non_default_keys(build_config)

                # Only show the tool dropdown if not in tool_mode
                if not is_in_tool_mode:
                    build_config["tool"]["show"] = True
                    if cached_tools:
                        # Use cached tools to populate options immediately
                        build_config["tool"]["options"] = [tool.name for tool in cached_tools]
                        build_config["tool"]["placeholder"] = "Select a tool"
                    else:
                        # Actually fetch tools now instead of deferring to a frontend callback.
                        # The frontend has no reliable mechanism to trigger a second
                        # update_build_config call for the "tool" field after this response,
                        # so we must populate the options here.
                        try:
                            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list(
                                mcp_server_value=field_value
                            )
                            build_config["tool"]["options"] = [tool.name for tool in self.tools]
                            build_config["tool"]["placeholder"] = "Select a tool"
                        except (TimeoutError, asyncio.TimeoutError) as e:
                            msg = f"Timeout loading tools for MCP server: {e!s}"
                            await logger.awarning(msg)
                            build_config["tool"]["options"] = []
                            build_config["tool"]["placeholder"] = "Timeout on MCP server"
                        except (ValueError, ImportError, ConnectionError, OSError, RuntimeError) as e:
                            msg = f"Error loading tools for MCP server: {e!s}"
                            await logger.awarning(msg)
                            build_config["tool"]["options"] = []
                            build_config["tool"]["placeholder"] = "Error on MCP Server"
                    # Force a value refresh only when the user genuinely switched servers.
                    # server_changed is only True for real user-initiated changes (not initial load).
                    if server_changed:
                        build_config["tool"]["value"] = uuid.uuid4()
                else:
                    # Keep the tool dropdown hidden if in tool_mode
                    self._not_load_actions = True
                    build_config["tool"]["show"] = False

            elif field_name == "tool_mode":
                build_config["tool"]["placeholder"] = ""
                build_config["tool"]["show"] = not bool(field_value) and bool(build_config["mcp_server"])
                self.remove_non_default_keys(build_config)
                self.tool = build_config["tool"]["value"]
                if field_value:
                    self._not_load_actions = True
                else:
                    build_config["tool"]["value"] = uuid.uuid4()
                    build_config["tool"]["show"] = True
                    # Fetch tools immediately instead of showing "Loading tools..."
                    try:
                        self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()
                        build_config["tool"]["options"] = [tool.name for tool in self.tools]
                        build_config["tool"]["placeholder"] = "Select a tool"
                    except (TimeoutError, asyncio.TimeoutError) as e:
                        msg = f"Timeout loading tools when toggling tool mode: {e!s}"
                        await logger.awarning(msg)
                        build_config["tool"]["options"] = []
                        build_config["tool"]["placeholder"] = "Timeout on MCP server"
                    except (ValueError, ImportError, ConnectionError, OSError, RuntimeError) as e:
                        msg = f"Error loading tools when toggling tool mode: {e!s}"
                        await logger.awarning(msg)
                        build_config["tool"]["options"] = []
                        build_config["tool"]["placeholder"] = "Error on MCP Server"
            elif field_name == "tools_metadata":
                self._not_load_actions = False

        except Exception as e:
            msg = f"Error in update_build_config: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
        else:
            return build_config