def _get_tool_response_str(self, tool_response) -> str:
        """Convert various tool response formats to a string representation."""
        if isinstance(tool_response, str):
            tool_response_str = tool_response
        elif isinstance(tool_response, Data):
            tool_response_str = str(tool_response.data)
        elif isinstance(tool_response, list) and all(isinstance(item, Data) for item in tool_response):
            # get only the first element, not 100% sure if it should be the first or the last
            tool_response_str = str(tool_response[0].data)
        elif isinstance(tool_response, (dict, list)):
            tool_response_str = str(tool_response)
        else:
            # Return empty string instead of None to avoid type errors
            tool_response_str = str(tool_response) if tool_response is not None else ""

        return tool_response_str