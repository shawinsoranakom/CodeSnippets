async def connect_http(
        self,
        server: RemoteMCPServer,
        conversation_id: str | None = None,
        timeout: float = 30.0,
    ):
        """Connect to MCP server using streamable HTTP or SSE transport."""
        server_url = server.url
        api_key = (
            str(server.auth) if server.auth else None
        )  # SDK uses `auth` for bearer token

        if not server_url:
            raise ValueError('Server URL is required.')

        transport_type = server.transport or 'http'

        try:
            headers: dict[str, str] = (
                {k: str(v) for k, v in server.headers.items()} if server.headers else {}
            )
            if api_key:
                headers.update(
                    {
                        'Authorization': f'Bearer {api_key}',
                        's': api_key,
                        'X-Session-API-Key': api_key,
                    }
                )

            if conversation_id:
                headers['X-OpenHands-ServerConversation-ID'] = conversation_id

            transport: SSETransport | StreamableHttpTransport
            if transport_type == 'sse':
                transport = SSETransport(
                    url=server_url,
                    headers=headers or None,
                )
            else:
                transport = StreamableHttpTransport(
                    url=server_url,
                    headers=headers or None,
                )
            self.client = Client(transport, timeout=timeout)

            await self._initialize_and_list_tools()
        except McpError as e:
            error_msg = f'McpError connecting to {server_url}: {e}'
            logger.error(error_msg)
            mcp_error_collector.add_error(
                server_name=server_url,
                server_type=transport_type,
                error_message=error_msg,
                exception_details=str(e),
            )
            raise

        except Exception as e:
            error_msg = f'Error connecting to {server_url}: {e}'
            logger.error(error_msg)
            mcp_error_collector.add_error(
                server_name=server_url,
                server_type=transport_type,
                error_message=error_msg,
                exception_details=str(e),
            )
            raise