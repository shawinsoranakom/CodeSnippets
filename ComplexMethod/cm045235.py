def _add_tools(self, tools: Optional[ListToolType], converted_tools: List[ToolDefinition]) -> None:
        """
        Convert various tool formats to Azure AI Agent tool definitions.

        Args:
            tools: List of tools in various formats (string identifiers, ToolDefinition objects, Tool objects, or callables)
            converted_tools: List to which converted tool definitions will be added

        Raises:
            ValueError: If an unsupported tool type is provided
        """
        if tools is None:
            return

        for tool in tools:
            if isinstance(tool, str):
                if tool == "file_search":
                    converted_tools.append(FileSearchToolDefinition())
                elif tool == "code_interpreter":
                    converted_tools.append(CodeInterpreterToolDefinition())
                elif tool == "bing_grounding":
                    converted_tools.append(BingGroundingToolDefinition())  # type: ignore
                elif tool == "azure_ai_search":
                    converted_tools.append(AzureAISearchToolDefinition())
                elif tool == "azure_function":
                    converted_tools.append(AzureFunctionToolDefinition())  # type: ignore
                # elif tool == "sharepoint_grounding":
                #     converted_tools.append(SharepointToolDefinition())  # type: ignore
                else:
                    raise ValueError(f"Unsupported tool string: {tool}")
            elif isinstance(tool, ToolDefinition):
                converted_tools.append(tool)
            elif isinstance(tool, Tool):
                self._original_tools.append(tool)
                converted_tools.append(self._convert_tool_to_function_tool_definition(tool))
            elif callable(tool):
                if hasattr(tool, "__doc__") and tool.__doc__ is not None:
                    description = tool.__doc__
                else:
                    description = ""
                function_tool = FunctionTool(tool, description=description)
                self._original_tools.append(function_tool)
                converted_tools.append(self._convert_tool_to_function_tool_definition(function_tool))
            else:
                raise ValueError(f"Unsupported tool type: {type(tool)}")