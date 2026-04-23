async def _process_mcp_tasks(self, client_session: ClientSession | None, error_message: str | None = None) -> None:
        while not self._close:
            try:
                mcp_task, arguments, result_queue = await asyncio.wait_for(self._queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            logging.debug(f"Got MCP task {mcp_task} arguments {arguments}")

            r: Any = None

            if not client_session or error_message:
                r = ValueError(error_message)
                try:
                    await result_queue.put(r)
                except asyncio.CancelledError:
                    break
                continue

            try:
                if mcp_task == "list_tools":
                    r = await client_session.list_tools()
                elif mcp_task == "tool_call":
                    r = await client_session.call_tool(**arguments)
                else:
                    r = ValueError(f"Unknown MCP task {mcp_task}")
            except Exception as e:
                r = e
            except asyncio.CancelledError:
                break

            try:
                await result_queue.put(r)
            except asyncio.CancelledError:
                break