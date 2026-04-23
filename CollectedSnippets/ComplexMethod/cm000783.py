async def run(
        self,
        input_data: Input,
        *,
        user_id: str,
        credentials: OAuth2Credentials | None = None,
        **kwargs,
    ) -> BlockOutput:
        if not input_data.server_url:
            yield "error", "MCP server URL is required"
            return

        if not input_data.selected_tool:
            yield "error", "No tool selected. Please select a tool from the dropdown."
            return

        # Validate required tool arguments before calling the server.
        # The executor-level validation is bypassed for MCP blocks because
        # get_input_defaults() flattens tool_arguments, stripping tool_input_schema
        # from the validation context.
        required = set(input_data.tool_input_schema.get("required", []))
        if required:
            missing = required - set(input_data.tool_arguments.keys())
            if missing:
                yield "error", (
                    f"Missing required argument(s): {', '.join(sorted(missing))}. "
                    f"Please fill in all required fields marked with * in the block form."
                )
                return

        # If no credentials were injected by the executor (e.g. legacy nodes
        # that don't have the credentials field set), try to auto-lookup
        # the stored MCP credential for this server URL.
        if credentials is None:
            credentials = await self._auto_lookup_credential(
                user_id, normalize_mcp_url(input_data.server_url)
            )

        auth_token = (
            credentials.access_token.get_secret_value() if credentials else None
        )

        try:
            result = await self._call_mcp_tool(
                server_url=input_data.server_url,
                tool_name=input_data.selected_tool,
                arguments=input_data.tool_arguments,
                auth_token=auth_token,
            )
            yield "result", result
        except MCPClientError as e:
            yield "error", str(e)
        except Exception as e:
            logger.exception(f"MCP tool call failed: {e}")
            yield "error", f"MCP tool call failed: {str(e)}"