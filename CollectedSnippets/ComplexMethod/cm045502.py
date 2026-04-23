async def handle_operation(self, operation: Dict[str, Any]) -> None:
        """Handle an MCP operation - this preserves the exact behavior of handle_mcp_operation"""
        operation_type = operation.get("operation")

        try:
            if operation_type == "list_tools":
                result = await self.session.list_tools()
                tools_data = [serialize_for_json(tool.model_dump()) for tool in result.tools]
                await self.event_handler.on_operation_result("list_tools", {"tools": tools_data})

            elif operation_type == "call_tool":
                tool_name = operation.get("tool_name")
                arguments = operation.get("arguments", {})
                if not tool_name:
                    raise McpOperationError("Tool name is required")

                result = await self.session.call_tool(tool_name, arguments)
                await self.event_handler.on_operation_result(
                    "call_tool", {"tool_name": tool_name, "result": serialize_for_json(result.model_dump())}
                )

            elif operation_type == "list_resources":
                result = await self.session.list_resources()
                await self.event_handler.on_operation_result("list_resources", serialize_for_json(result.model_dump()))

            elif operation_type == "read_resource":
                uri = operation.get("uri")
                if not uri:
                    raise McpOperationError("Resource URI is required")

                result = await self.session.read_resource(uri)
                await self.event_handler.on_operation_result("read_resource", serialize_for_json(result.model_dump()))

            elif operation_type == "list_prompts":
                result = await self.session.list_prompts()
                prompts_data = [serialize_for_json(prompt.model_dump()) for prompt in result.prompts]
                await self.event_handler.on_operation_result("list_prompts", {"prompts": prompts_data})

            elif operation_type == "get_prompt":
                name = operation.get("name")
                arguments = operation.get("arguments")
                if not name:
                    raise McpOperationError("Prompt name is required")

                result = await self.session.get_prompt(name, arguments)
                await self.event_handler.on_operation_result("get_prompt", serialize_for_json(result.model_dump()))

            else:
                await self.event_handler.on_operation_error(
                    operation_type or "unknown", f"Unknown operation: {operation_type}"
                )

        except Exception as e:
            real_error = extract_real_error(e)
            await self.event_handler.on_operation_error(operation_type or "unknown", real_error)