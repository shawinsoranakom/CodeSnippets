async def _run_actor(self) -> None:
        result: McpResult
        try:
            async with create_mcp_server_session(
                self.server_params,
                sampling_callback=self._sampling_callback,
                elicitation_callback=self._elicitation_callback,
                list_roots_callback=self._list_roots,
            ) as session:
                # Save the initialize result
                self._initialize_result = await session.initialize()
                while True:
                    cmd = await self._command_queue.get()
                    if cmd["type"] == "shutdown":
                        cmd["future"].set_result("ok")
                        break
                    elif cmd["type"] == "call_tool":
                        try:
                            result = session.call_tool(name=cmd["name"], arguments=cmd["args"])
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "read_resource":
                        try:
                            result = session.read_resource(uri=cmd["uri"])
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "get_prompt":
                        try:
                            result = session.get_prompt(name=cmd["name"], arguments=cmd["args"])
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "list_tools":
                        try:
                            result = session.list_tools()
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "list_prompts":
                        try:
                            result = session.list_prompts()
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "list_resources":
                        try:
                            result = session.list_resources()
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
                    elif cmd["type"] == "list_resource_templates":
                        try:
                            result = session.list_resource_templates()
                            cmd["future"].set_result(result)
                        except Exception as e:
                            cmd["future"].set_exception(e)
        except Exception as e:
            try:
                while True:
                    try:
                        pending_cmd = self._command_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    fut = pending_cmd.get("future")
                    if fut is not None and not fut.done():
                        fut.set_exception(e)
            except Exception:
                # Best-effort draining only
                pass

            if self._shutdown_future and not self._shutdown_future.done():
                self._shutdown_future.set_exception(e)
            else:
                logger.exception("Exception in MCP actor task")
        finally:
            self._active = False
            self._actor_task = None