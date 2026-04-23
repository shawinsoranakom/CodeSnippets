def get_mcp_config(
        self, extra_stdio_servers: dict[str, StdioMCPServer] | None = None
    ) -> MCPConfig:
        import sys

        if sys.platform == 'win32':
            self.log('debug', 'MCP is disabled on Windows, returning empty config')
            return MCPConfig(mcpServers={})

        updated_mcp_config = self.config.mcp.model_copy()

        # Collect current stdio servers from config + extras
        current_stdio: dict[str, StdioMCPServer] = {
            name: server
            for name, server in updated_mcp_config.mcpServers.items()
            if isinstance(server, StdioMCPServer)
        }
        if extra_stdio_servers:
            current_stdio.update(extra_stdio_servers)

        # Find servers not yet sent to the action execution server
        new_servers = {
            name: server
            for name, server in current_stdio.items()
            if name not in self._last_updated_mcp_stdio_servers
        }

        self.log(
            'debug',
            f'adding {len(new_servers)} new stdio servers to MCP config: {list(new_servers.keys())}',
        )

        if new_servers:
            # Merge current + previously-sent for the update payload
            combined = {**self._last_updated_mcp_stdio_servers, **current_stdio}

            stdio_tools = [
                {'name': name, **server.model_dump(mode='json')}
                for name, server in sorted(combined.items())
            ]

            self.log(
                'debug',
                f'Updating MCP server with {len(new_servers)} new stdio servers (total: {len(combined)})',
            )
            response = self._send_action_server_request(
                'POST',
                f'{self.action_execution_server_url}/update_mcp_server',
                json=stdio_tools,
                timeout=60,
            )
            result = response.json()
            if response.status_code != 200:
                self.log('warning', f'Failed to update MCP server: {response.text}')
            else:
                if result.get('router_error_log'):
                    self.log(
                        'warning',
                        f'Some MCP servers failed to be added: {result["router_error_log"]}',
                    )
                self._last_updated_mcp_stdio_servers = dict(combined)
                self.log(
                    'debug',
                    f'Successfully updated MCP stdio servers, now tracking {len(combined)} servers',
                )
            self.log(
                'info',
                f'Updated MCP config: {list(updated_mcp_config.mcpServers.keys())}',
            )
        else:
            self.log('debug', 'No new stdio servers to update')

        # Expose the runtime's MCP SSE proxy when stdio servers exist
        if self._last_updated_mcp_stdio_servers:
            updated_mcp_config.mcpServers['_runtime_proxy'] = RemoteMCPServer(
                url=self.action_execution_server_url.rstrip('/') + '/mcp/sse',
                transport='sse',
                auth=self.session_api_key,
            )

        return updated_mcp_config