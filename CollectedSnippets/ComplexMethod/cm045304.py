async def list_tools(self) -> List[ToolSchema]:
        if not self._actor:
            await self.start()  # fallback to start the actor if not initialized instead of raising an error
            # Why? Because when deserializing the workbench, the actor might not be initialized yet.
            # raise RuntimeError("Actor is not initialized. Call start() first.")
        if self._actor is None:
            raise RuntimeError("Actor is not initialized. Please check the server connection.")
        result_future = await self._actor.call("list_tools", None)
        list_tool_result = await result_future
        assert isinstance(
            list_tool_result, ListToolsResult
        ), f"list_tools must return a CallToolResult, instead of : {str(type(list_tool_result))}"
        schema: List[ToolSchema] = []
        for tool in list_tool_result.tools:
            original_name = tool.name
            name = original_name
            description = tool.description or ""

            # Apply overrides if they exist for this tool
            if original_name in self._tool_overrides:
                override = self._tool_overrides[original_name]
                if override.name is not None:
                    name = override.name
                if override.description is not None:
                    description = override.description

            parameters = ParametersSchema(
                type="object",
                properties=tool.inputSchema.get("properties", {}),
                required=tool.inputSchema.get("required", []),
                additionalProperties=tool.inputSchema.get("additionalProperties", False),
            )
            tool_schema = ToolSchema(
                name=name,
                description=description,
                parameters=parameters,
            )
            schema.append(tool_schema)
        return schema