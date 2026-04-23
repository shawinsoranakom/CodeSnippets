async def build_output(self) -> DataFrame:
        """Build output with improved error handling and validation."""
        try:
            self.tools, _ = await self.update_tool_list()
            if self.tool != "":
                # Set session context for persistent MCP sessions using Langflow session ID
                session_context = self._get_session_context()
                if session_context:
                    self.stdio_client.set_session_context(session_context)
                    self.streamable_http_client.set_session_context(session_context)
                exec_tool = self._tool_cache[self.tool]
                kwargs = self._build_tool_kwargs(exec_tool.args_schema)
                unflattened_kwargs = maybe_unflatten_dict(kwargs)

                output = await exec_tool.coroutine(**unflattened_kwargs)
                tool_content = []
                for item in output.content:
                    item_dict = item.model_dump()
                    item_dict = self.process_output_item(item_dict)
                    tool_content.append(item_dict)

                if isinstance(tool_content, list) and all(isinstance(x, dict) for x in tool_content):
                    return DataFrame(tool_content)
                return DataFrame(data=tool_content)
            return DataFrame(data=[{"error": "You must select a tool"}])
        except Exception as e:
            msg = f"Error in build_output: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e