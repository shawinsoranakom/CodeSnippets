async def call(self, type: str, args: McpActorArgs | None = None) -> McpFuture:
        if not self._active:
            raise RuntimeError("MCP Actor not running, call initialize() first")
        if self._actor_task and self._actor_task.done():
            raise RuntimeError("MCP actor task crashed", self._actor_task.exception())
        fut: asyncio.Future[McpFuture] = asyncio.Future()
        if type in {"list_tools", "list_prompts", "list_resources", "list_resource_templates", "shutdown"}:
            await self._command_queue.put({"type": type, "future": fut})
            res = await fut
        elif type in {"call_tool", "read_resource", "get_prompt"}:
            if args is None:
                raise ValueError(f"args is required for {type}")
            name = args.get("name", None)
            kwargs = args.get("kargs", {})
            if type == "call_tool" and name is None:
                raise ValueError("name is required for call_tool")
            elif type == "read_resource":
                uri = kwargs.get("uri", None)
                if uri is None:
                    raise ValueError("uri is required for read_resource")
                await self._command_queue.put({"type": type, "uri": uri, "future": fut})
            elif type == "get_prompt":
                if name is None:
                    raise ValueError("name is required for get_prompt")
                prompt_args = kwargs.get("arguments", None)
                await self._command_queue.put({"type": type, "name": name, "args": prompt_args, "future": fut})
            else:  # call_tool
                await self._command_queue.put({"type": type, "name": name, "args": kwargs, "future": fut})
            res = await fut
        else:
            raise ValueError(f"Unknown command type: {type}")
        return res