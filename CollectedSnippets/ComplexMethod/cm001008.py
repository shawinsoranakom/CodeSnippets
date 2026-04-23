async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        server_url: str = "",
        tool_name: str = "",
        tool_arguments: dict[str, Any] | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        server_url = server_url.strip()
        tool_name = tool_name.strip()
        session_id = session.session_id

        # Session-level dry_run prevents real MCP tool execution.
        # Discovery (no tool_name) is still allowed so the agent can inspect
        # available tools, but actual execution is blocked.
        if session.dry_run and tool_name:
            return MCPToolOutputResponse(
                message=(
                    f"[dry-run] MCP tool '{tool_name}' on "
                    f"{server_host(server_url)} was not executed "
                    "because the session is in dry-run mode."
                ),
                server_url=server_url,
                tool_name=tool_name,
                result=None,
                success=True,
                session_id=session_id,
            )

        if tool_arguments is not None and not isinstance(tool_arguments, dict):
            return ErrorResponse(
                message="tool_arguments must be a JSON object.",
                session_id=session_id,
            )
        resolved_tool_arguments: dict[str, Any] = (
            tool_arguments if isinstance(tool_arguments, dict) else {}
        )

        if not server_url:
            return ErrorResponse(
                message="Please provide a server_url for the MCP server.",
                session_id=session_id,
            )

        _parsed = urlparse(server_url)
        if _parsed.username or _parsed.password:
            return ErrorResponse(
                message=(
                    "Do not include credentials in server_url. "
                    "Use the MCP credential setup flow instead."
                ),
                session_id=session_id,
            )
        if _parsed.query or _parsed.fragment:
            return ErrorResponse(
                message=(
                    "Do not include query parameters or fragments in server_url. "
                    "Use the MCP credential setup flow instead."
                ),
                session_id=session_id,
            )

        if not user_id:
            return ErrorResponse(
                message="Authentication required.",
                session_id=session_id,
            )

        # Validate URL to prevent SSRF — blocks loopback and private IP ranges
        try:
            await validate_url_host(server_url)
        except ValueError as e:
            msg = str(e)
            if "Unable to resolve" in msg or "No IP addresses" in msg:
                user_msg = (
                    f"Hostname not found: {server_host(server_url)}. "
                    "Please check the URL — the domain may not exist."
                )
            else:
                user_msg = f"Blocked server URL: {msg}"
            return ErrorResponse(message=user_msg, session_id=session_id)

        # Fast DB lookup — no network call.
        # Normalize for matching because stored credentials use normalized URLs.
        creds = await auto_lookup_mcp_credential(user_id, normalize_mcp_url(server_url))
        auth_token = creds.access_token.get_secret_value() if creds else None

        client = MCPClient(server_url, auth_token=auth_token)

        try:
            await client.initialize()

            if not tool_name:
                # Stage 1: Discover available tools
                return await self._discover_tools(client, server_url, session_id)
            else:
                # Stage 2: Execute the selected tool
                return await self._execute_tool(
                    client, server_url, tool_name, resolved_tool_arguments, session_id
                )

        except HTTPClientError as e:
            if e.status_code in _AUTH_STATUS_CODES and not creds:
                # Server requires auth and user has no stored credentials
                return self._build_setup_requirements(server_url, session_id)
            host = server_host(server_url)
            logger.warning("MCP HTTP error for %s: status=%s", host, e.status_code)
            return ErrorResponse(
                message=(f"MCP request to {host} failed with HTTP {e.status_code}."),
                session_id=session_id,
                error=f"HTTP {e.status_code}: {str(e)[:300]}",
            )

        except MCPClientError as e:
            logger.warning("MCP client error for %s: %s", server_host(server_url), e)
            return ErrorResponse(
                message=str(e),
                session_id=session_id,
            )

        except Exception:
            logger.error(
                "Unexpected error calling MCP server %s",
                server_host(server_url),
                exc_info=True,
            )
            return ErrorResponse(
                message="An unexpected error occurred connecting to the MCP server. Please try again.",
                session_id=session_id,
            )