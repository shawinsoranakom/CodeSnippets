def test_tool_choice(self, model: BaseChatModel) -> None:
        """Test `tool_choice` parameter.

        Test that the model can force tool calling via the `tool_choice`
        parameter. This test is skipped if the `has_tool_choice` property on the
        test class is set to `False`.

        This test is optional and should be skipped if the model does not support
        tool calling (see configuration below).

        ??? note "Configuration"

            To disable tool calling tests, set `has_tool_choice` to `False` in your
            test class:

            ```python
            class TestMyChatModelIntegration(ChatModelIntegrationTests):
                @property
                def has_tool_choice(self) -> bool:
                    return False
            ```

        ??? question "Troubleshooting"

            If this test fails, check whether the `test_tool_calling` test is passing.
            If it is not, refer to the troubleshooting steps in that test first.

            If `test_tool_calling` is passing, check that the underlying model
            supports forced tool calling. If it does, `bind_tools` should accept a
            `tool_choice` parameter that can be used to force a tool call.

            It should accept (1) the string `'any'` to force calling the bound tool,
            and (2) the string name of the tool to force calling that tool.

        """
        if not self.has_tool_choice or not self.has_tool_calling:
            pytest.skip("Test requires tool choice.")

        @tool
        def get_weather(location: str) -> str:  # noqa: ARG001
            """Get weather at a location."""
            return "It's sunny."

        for tool_choice in ["any", "magic_function"]:
            model_with_tools = model.bind_tools(
                [magic_function, get_weather], tool_choice=tool_choice
            )
            result = model_with_tools.invoke("Hello!")
            assert isinstance(result, AIMessage)
            assert result.tool_calls
            if tool_choice == "magic_function":
                assert result.tool_calls[0]["name"] == "magic_function"