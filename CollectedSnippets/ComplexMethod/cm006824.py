def update_tools_metadata(
        self,
        tools: list[BaseTool | StructuredTool],
    ) -> list[BaseTool]:
        # update the tool_name and description according to the name and secriotion mentioned in the list
        if isinstance(self.metadata, pd.DataFrame):
            metadata_dict = self.get_tools_metadata_dictionary()
            filtered_tools = []
            for tool in tools:
                if isinstance(tool, StructuredTool | BaseTool) and tool.tags:
                    try:
                        tag = tool.tags[0]
                    except IndexError:
                        msg = "Tool tags cannot be empty."
                        raise ValueError(msg) from None
                    if tag in metadata_dict:
                        tool_metadata = metadata_dict[tag]
                        # Only include tools with status=True
                        if tool_metadata.get("status", True):
                            tool.name = tool_metadata.get("name", tool.name)
                            tool.description = tool_metadata.get("description", tool.description)
                            if tool_metadata.get("commands"):
                                tool.description = _add_commands_to_tool_description(
                                    tool.description, tool_metadata.get("commands")
                                )
                            filtered_tools.append(tool)
                else:
                    msg = f"Expected a StructuredTool or BaseTool, got {type(tool)}"
                    raise TypeError(msg)
            return filtered_tools
        return tools