async def disconnect(self, server_id: str = "") -> None:
        """Disconnect from a specific MCP server or all servers if no server_id provided."""
        if server_id:
            if server_id in self.sessions:
                try:
                    exit_stack = self.exit_stacks.get(server_id)

                    # Close the exit stack which will handle session cleanup
                    if exit_stack:
                        try:
                            await exit_stack.aclose()
                        except RuntimeError as e:
                            if "cancel scope" in str(e).lower():
                                logger.warning(
                                    f"Cancel scope error during disconnect from {server_id}, continuing with cleanup: {e}"
                                )
                            else:
                                raise

                    # Clean up references
                    self.sessions.pop(server_id, None)
                    self.exit_stacks.pop(server_id, None)

                    # Remove tools associated with this server
                    self.tool_map = {
                        k: v
                        for k, v in self.tool_map.items()
                        if v.server_id != server_id
                    }
                    self.tools = tuple(self.tool_map.values())
                    logger.info(f"Disconnected from MCP server {server_id}")
                except Exception as e:
                    logger.error(f"Error disconnecting from server {server_id}: {e}")
        else:
            # Disconnect from all servers in a deterministic order
            for sid in sorted(list(self.sessions.keys())):
                await self.disconnect(sid)
            self.tool_map = {}
            self.tools = tuple()
            logger.info("Disconnected from all MCP servers")