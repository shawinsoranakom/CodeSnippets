async def _mcp_server_loop(self) -> None:
        url = self._mcp_server.url.strip()
        raw_headers: dict[str, str] = self._mcp_server.headers or {}
        custom_header: dict[str, str] = self._custom_header or {}
        headers: dict[str, str] = {}

        for h, v in raw_headers.items():
            nh = Template(h).safe_substitute(self._server_variables)
            nv = Template(v).safe_substitute(self._server_variables)
            if nh.strip() and nv.strip().strip("Bearer"):
                headers[nh] = nv

        for h, v in custom_header.items():
            nh = Template(h).safe_substitute(custom_header)
            nv = Template(v).safe_substitute(custom_header)
            headers[nh] = nv

        if self._mcp_server.server_type == MCPServerType.SSE:
            # SSE transport
            try:
                async with sse_client(url, headers) as stream:
                    async with ClientSession(*stream) as client_session:
                        try:
                            await asyncio.wait_for(client_session.initialize(), timeout=5)
                            logging.info("client_session initialized successfully")
                            await self._process_mcp_tasks(client_session)
                        except asyncio.TimeoutError:
                            msg = f"Timeout initializing client_session for server {self._mcp_server.id}"
                            logging.error(msg)
                            await self._process_mcp_tasks(None, msg)
                        except asyncio.CancelledError:
                            logging.warning(f"SSE transport MCP session cancelled for server {self._mcp_server.id}")
                            return
            except Exception:
                msg = "Connection failed (possibly due to auth error). Please check authentication settings first"
                await self._process_mcp_tasks(None, msg)

        elif self._mcp_server.server_type == MCPServerType.STREAMABLE_HTTP:
            # Streamable HTTP transport
            try:
                async with streamablehttp_client(url, headers) as (read_stream, write_stream, _):
                    async with ClientSession(read_stream, write_stream) as client_session:
                        try:
                            await asyncio.wait_for(client_session.initialize(), timeout=5)
                            logging.info("client_session initialized successfully")
                            await self._process_mcp_tasks(client_session)
                        except asyncio.TimeoutError:
                            msg = f"Timeout initializing client_session for server {self._mcp_server.id}"
                            logging.error(msg)
                            await self._process_mcp_tasks(None, msg)
                        except asyncio.CancelledError:
                            logging.warning(f"STREAMABLE_HTTP MCP session cancelled for server {self._mcp_server.id}")
                            return
            except Exception as e:
                logging.exception(e)
                msg = "Connection failed (possibly due to auth error). Please check authentication settings first"
                await self._process_mcp_tasks(None, msg)

        else:
            await self._process_mcp_tasks(None,
                                          f"Unsupported MCP server type: {self._mcp_server.server_type}, id: {self._mcp_server.id}")