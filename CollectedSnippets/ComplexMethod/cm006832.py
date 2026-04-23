async def update_tools(
    server_name: str,
    server_config: dict,
    mcp_stdio_client: MCPStdioClient | None = None,
    mcp_streamable_http_client: MCPStreamableHttpClient | None = None,
    mcp_sse_client: MCPStreamableHttpClient | None = None,  # Backward compatibility
    request_variables: dict[str, str] | None = None,
) -> tuple[str, list[StructuredTool], dict[str, StructuredTool]]:
    """Fetch server config and update available tools.

    Args:
        server_name: Name of the MCP server
        server_config: Server configuration dictionary
        mcp_stdio_client: Optional stdio client instance
        mcp_streamable_http_client: Optional streamable HTTP client instance
        mcp_sse_client: Optional SSE client instance (backward compatibility)
        request_variables: Optional dict of global variables to resolve in headers
    """
    if server_config is None:
        server_config = {}
    if not server_name:
        return "", [], {}
    if mcp_stdio_client is None:
        mcp_stdio_client = MCPStdioClient()

    # Backward compatibility: accept mcp_sse_client parameter
    if mcp_streamable_http_client is None:
        mcp_streamable_http_client = mcp_sse_client if mcp_sse_client is not None else MCPStreamableHttpClient()

    # Fetch server config from backend
    # Determine mode from config, defaulting to Streamable_HTTP if URL present
    mode = server_config.get("mode", "")
    if not mode:
        mode = "Stdio" if "command" in server_config else "Streamable_HTTP" if "url" in server_config else ""

    command = server_config.get("command", "")
    url = server_config.get("url", "")
    tools = []
    headers = _process_headers(server_config.get("headers", {}), request_variables)

    try:
        await _validate_connection_params(mode, command, url)
    except ValueError as e:
        logger.error(f"Invalid MCP server configuration for '{server_name}': {e}")
        raise

    # Determine connection type and parameters
    client: MCPStdioClient | MCPStreamableHttpClient | None = None
    if mode == "Stdio":
        args = list(server_config.get("args", []))
        env = server_config.get("env", {})
        # For stdio mode, inject component headers as --headers CLI args.
        # This enables passing headers through proxy tools like mcp-proxy
        # that forward them to the upstream HTTP server.
        if headers:
            extra_args = []
            for key, value in headers.items():
                extra_args.extend(["--headers", key, str(value)])
            if "--headers" in args:
                # Insert before the existing --headers flag so all header
                # flags are grouped together
                idx = args.index("--headers")
                for i, arg in enumerate(extra_args):
                    args.insert(idx + i, arg)
            else:
                # No existing --headers flag; try to insert before the last
                # positional arg (typically the URL in mcp-proxy commands).
                # Scan args to find the last true positional token by skipping
                # flag+value pairs so we don't mistake a flag's value for a
                # positional argument (e.g. "--port 8080").
                last_positional_idx: int | None = None
                i = 0
                while i < len(args):
                    if args[i].startswith("-"):
                        # Skip the flag and its value (assumes each flag
                        # takes at most one value argument; boolean flags
                        # are handled correctly since the next token will
                        # start with '-' or be a URL-like positional).
                        i += 1
                        if (
                            i < len(args)
                            and not args[i].startswith("-")
                            and not args[i].startswith("http://")
                            and not args[i].startswith("https://")
                        ):
                            i += 1
                    else:
                        last_positional_idx = i
                        i += 1

                if last_positional_idx is not None:
                    args = args[:last_positional_idx] + extra_args + args[last_positional_idx:]
                else:
                    args.extend(extra_args)
        full_command = shlex.join([*shlex.split(command), *args])
        tools = await mcp_stdio_client.connect_to_server(full_command, env)
        client = mcp_stdio_client
    elif mode in ["Streamable_HTTP", "SSE"]:
        # Streamable HTTP connection with SSE fallback
        verify_ssl = server_config.get("verify_ssl", True)
        tools = await mcp_streamable_http_client.connect_to_server(url, headers=headers, verify_ssl=verify_ssl)
        client = mcp_streamable_http_client
    else:
        logger.error(f"Invalid MCP server mode for '{server_name}': {mode}")
        return "", [], {}

    if not tools or not client or not client._connected:
        logger.warning(f"No tools available from MCP server '{server_name}' or connection failed")
        return "", [], {}

    tool_list = []
    tool_cache: dict[str, StructuredTool] = {}
    for tool in tools:
        if not tool or not hasattr(tool, "name"):
            continue
        try:
            args_schema = create_input_schema_from_json_schema(tool.inputSchema)
            if not args_schema:
                logger.warning(f"Could not create schema for tool '{tool.name}' from server '{server_name}'")
                continue

            # Create a custom StructuredTool that bypasses schema validation
            class MCPStructuredTool(StructuredTool):
                _tool_call_id_key = "_lf_tool_call_id"

                def _to_args_and_kwargs(
                    self, tool_input: str | dict, tool_call_id: str | None
                ) -> tuple[tuple, dict[str, Any]]:
                    """Normalize MCP tool input before LangChain validates it."""
                    if isinstance(tool_input, str):
                        try:
                            parsed_input = json.loads(tool_input)
                        except json.JSONDecodeError:
                            parsed_input = {"input": tool_input}
                    else:
                        parsed_input = tool_input or {}

                    converted_input = self._convert_parameters(parsed_input)
                    tool_args, tool_kwargs = super()._to_args_and_kwargs(converted_input, tool_call_id)
                    if tool_call_id is not None:
                        tool_kwargs[self._tool_call_id_key] = tool_call_id
                    return tool_args, tool_kwargs

                def _run(self, *args: Any, config: RunnableConfig, run_manager=None, **kwargs: Any) -> tuple[Any, Any]:
                    """Return converted content plus the raw MCP result as artifact."""
                    tool_call_id = kwargs.pop(self._tool_call_id_key, None)
                    raw = super()._run(*args, config=config, run_manager=run_manager, **kwargs)
                    content = _convert_mcp_result(raw) if tool_call_id and hasattr(raw, "content") else raw
                    return content, raw

                async def _arun(
                    self, *args: Any, config: RunnableConfig, run_manager=None, **kwargs: Any
                ) -> tuple[Any, Any]:
                    """Return converted content plus the raw MCP result as artifact."""
                    tool_call_id = kwargs.pop(self._tool_call_id_key, None)
                    raw = await super()._arun(*args, config=config, run_manager=run_manager, **kwargs)
                    content = _convert_mcp_result(raw) if tool_call_id and hasattr(raw, "content") else raw
                    return content, raw

                def _convert_parameters(self, input_dict):
                    if not input_dict or not isinstance(input_dict, dict):
                        return input_dict

                    converted_dict = {}
                    original_fields = set(self.args_schema.model_fields.keys())

                    for key, value in input_dict.items():
                        if key in original_fields:
                            # Field exists as-is
                            converted_dict[key] = value
                        else:
                            # Try to convert camelCase to snake_case
                            snake_key = _camel_to_snake(key)
                            if snake_key in original_fields:
                                converted_dict[snake_key] = value
                            else:
                                # Keep original key (may be flattened e.g. params.search)
                                converted_dict[key] = value

                    unflattened = maybe_unflatten_dict(converted_dict)
                    # Normalize: convert JSON strings to dict for nested model params
                    normalized = _normalize_arguments_for_mcp(unflattened, self.args_schema, self.name)
                    # Preserve extra keys not in schema (e.g. flattened keys)
                    schema_fields = set(self.args_schema.model_fields.keys())
                    for key, value in unflattened.items():
                        if key not in schema_fields and key not in normalized:
                            normalized[key] = value
                    return normalized

            tool_obj = MCPStructuredTool(
                name=tool.name,
                description=tool.description or "",
                args_schema=args_schema,
                func=create_tool_func(tool.name, args_schema, client),
                coroutine=create_tool_coroutine(tool.name, args_schema, client),
                tags=[tool.name],
                metadata={"server_name": server_name, "output_schema": getattr(tool, "outputSchema", None)},
                response_format="content_and_artifact",
            )

            tool_list.append(tool_obj)
            tool_cache[tool.name] = tool_obj
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.error(f"Failed to create tool '{tool.name}' from server '{server_name}': {e}")
            msg = f"Failed to create tool '{tool.name}' from server '{server_name}': {e}"
            raise ValueError(msg) from e
        except (TypeError, AttributeError, KeyError, NameError, RecursionError) as e:
            # Per-tool resilience (#11229): isolate one bad schema, keep the rest of the toolset.
            logger.exception(
                f"Skipping tool '{getattr(tool, 'name', '<unknown>')}' from MCP server "
                f"'{server_name}' due to schema-processing error: "
                f"{type(e).__name__}: {e}. inputSchema={getattr(tool, 'inputSchema', None)!r}"
            )
            continue

    logger.info(f"Successfully loaded {len(tool_list)} tools from MCP server '{server_name}'")
    return mode, tool_list, tool_cache