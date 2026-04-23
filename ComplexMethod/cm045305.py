async def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        call_id: str | None = None,
    ) -> ToolResult:
        if not self._actor:
            await self.start()  # fallback to start the actor if not initialized instead of raising an error
            # Why? Because when deserializing the workbench, the actor might not be initialized yet.
            # raise RuntimeError("Actor is not initialized. Call start() first.")
        if self._actor is None:
            raise RuntimeError("Actor is not initialized. Please check the server connection.")
        if not cancellation_token:
            cancellation_token = CancellationToken()
        if not arguments:
            arguments = {}

        # Check if the name is an override name and map it back to the original
        original_name = self._override_name_to_original.get(name, name)

        with trace_tool_span(
            tool_name=name,  # Use the requested name for tracing
            tool_call_id=call_id,
        ):
            try:
                result_future = await self._actor.call("call_tool", {"name": original_name, "kargs": arguments})
                cancellation_token.link_future(result_future)
                result = await result_future
                assert isinstance(
                    result, CallToolResult
                ), f"call_tool must return a CallToolResult, instead of : {str(type(result))}"
                result_parts: List[TextResultContent | ImageResultContent] = []
                is_error = result.isError
                for content in result.content:
                    if isinstance(content, TextContent):
                        result_parts.append(TextResultContent(content=content.text))
                    elif isinstance(content, ImageContent):
                        result_parts.append(ImageResultContent(content=Image.from_base64(content.data)))
                    elif isinstance(content, EmbeddedResource):
                        # TODO: how to handle embedded resources?
                        # For now we just use text representation.
                        result_parts.append(TextResultContent(content=content.model_dump_json()))
                    else:
                        raise ValueError(f"Unknown content type from server: {type(content)}")
            except Exception as e:
                error_message = self._format_errors(e)
                is_error = True
                result_parts = [TextResultContent(content=error_message)]
        return ToolResult(name=name, result=result_parts, is_error=is_error)