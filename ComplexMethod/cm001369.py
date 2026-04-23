def test_functions_converted_to_tools(self, provider, search_function):
        messages = [ChatMessage.user("search")]
        _, kwargs = provider._get_chat_completion_args(
            prompt_messages=messages, functions=[search_function]
        )
        assert "tools" in kwargs
        assert len(kwargs["tools"]) == 1
        tool = kwargs["tools"][0]
        assert tool["name"] == "web_search"
        assert tool["description"] == "Search the web"
        assert "input_schema" in tool
        assert "query" in tool["input_schema"]["properties"]
        assert tool["input_schema"]["required"] == ["query"]