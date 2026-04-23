def get_tools(
        self,
        tool_name: str | None = None,
        tool_description: str | None = None,
        callbacks: Callbacks | None = None,
        flow_mode_inputs: list[dotdict] | None = None,
    ) -> list[BaseTool]:
        from lfx.io.schema import create_input_schema, create_input_schema_from_dict

        tools = []
        for output in self.component.outputs:
            if self._should_skip_output(output):
                continue

            if not output.method:
                msg = f"Output {output.name} does not have a method defined"
                raise ValueError(msg)

            output_method: Callable = getattr(self.component, output.method)
            args_schema = None
            tool_mode_inputs = [_input for _input in self.component.inputs if getattr(_input, "tool_mode", False)]
            if flow_mode_inputs:
                args_schema = create_input_schema_from_dict(
                    inputs=flow_mode_inputs,
                    param_key="flow_tweak_data",
                )
            elif tool_mode_inputs:
                args_schema = create_input_schema(tool_mode_inputs)
            elif output.required_inputs:
                inputs = [
                    self.component.get_underscore_inputs()[input_name]
                    for input_name in output.required_inputs
                    if getattr(self.component, input_name) is None
                ]
                # If any of the required inputs are not in tool mode, this means
                # that when the tool is called it will raise an error.
                # so we should raise an error here.
                # TODO: This logic might need to be improved, example if the required is an api key.
                if not all(getattr(_input, "tool_mode", False) for _input in inputs):
                    non_tool_mode_inputs = [
                        input_.name
                        for input_ in inputs
                        if not getattr(input_, "tool_mode", False) and input_.name is not None
                    ]
                    non_tool_mode_inputs_str = ", ".join(non_tool_mode_inputs)
                    msg = (
                        f"Output '{output.name}' requires inputs that are not in tool mode. "
                        f"The following inputs are not in tool mode: {non_tool_mode_inputs_str}. "
                        "Please ensure all required inputs are set to tool mode."
                    )
                    raise ValueError(msg)
                args_schema = create_input_schema(inputs)

            else:
                args_schema = create_input_schema(self.component.inputs)

            name = f"{output.method}".strip(".")
            formatted_name = _format_tool_name(name)
            event_manager = self.component.get_event_manager()
            if asyncio.iscoroutinefunction(output_method):
                tools.append(
                    StructuredTool(
                        name=formatted_name,
                        description=build_description(self.component),
                        coroutine=_build_output_async_function(
                            self.component, output_method, event_manager, TOOL_OUTPUT_NAME
                        ),
                        args_schema=args_schema,
                        handle_tool_error=True,
                        callbacks=callbacks,
                        tags=[formatted_name],
                        metadata={
                            "display_name": formatted_name,
                            "display_description": build_description(self.component),
                        },
                    )
                )
            else:
                tools.append(
                    StructuredTool(
                        name=formatted_name,
                        description=build_description(self.component),
                        func=_build_output_function(self.component, output_method, event_manager, TOOL_OUTPUT_NAME),
                        args_schema=args_schema,
                        handle_tool_error=True,
                        callbacks=callbacks,
                        tags=[formatted_name],
                        metadata={
                            "display_name": formatted_name,
                            "display_description": build_description(self.component),
                        },
                    )
                )
        if len(tools) == 1 and (tool_name or tool_description):
            tool = tools[0]
            tool.name = _format_tool_name(str(tool_name)) or tool.name
            tool.description = tool_description or tool.description
            tool.tags = [tool.name]
        elif (tool_name or tool_description) and (flow_mode_inputs or len(tools) > 1):
            for tool in tools:
                tool.name = _format_tool_name(str(tool_name) + "_" + str(tool.name)) or tool.name
                tool.description = (
                    str(tool_description) + " Output details: " + str(tool.description)
                ) or tool.description
                tool.tags = [tool.name]
        return tools