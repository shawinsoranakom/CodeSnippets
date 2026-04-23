def test_unicode_tool_call_integration(
        self,
        model: BaseChatModel,
        *,
        tool_choice: str | None = None,
        force_tool_call: bool = True,
    ) -> None:
        r"""Generic integration test for Unicode characters in tool calls.

        Args:
            model: The chat model to test
            tool_choice: Tool choice parameter to pass to `bind_tools()`
                (provider-specific)
            force_tool_call: Whether to force a tool call
                (use `tool_choice=True` if None)

        Tests that Unicode characters in tool call arguments are preserved correctly,
        not escaped as `\\uXXXX` sequences.

        """
        if not self.has_tool_calling:
            pytest.skip("Test requires tool calling support.")

        # Configure tool choice based on provider capabilities
        if tool_choice is None and force_tool_call:
            tool_choice = "any"

        if tool_choice is not None:
            llm_with_tool = model.bind_tools(
                [unicode_customer], tool_choice=tool_choice
            )
        else:
            llm_with_tool = model.bind_tools([unicode_customer])

        # Test with Chinese characters
        msgs = [
            HumanMessage(
                "Create a customer named '你好啊集团' (Hello Group) - a Chinese "
                "technology company"
            )
        ]
        ai_msg = llm_with_tool.invoke(msgs)

        assert isinstance(ai_msg, AIMessage)
        assert isinstance(ai_msg.tool_calls, list)

        if force_tool_call:
            assert len(ai_msg.tool_calls) >= 1, (
                f"Expected at least 1 tool call, got {len(ai_msg.tool_calls)}"
            )

        if ai_msg.tool_calls:
            tool_call = ai_msg.tool_calls[0]
            assert tool_call["name"] == "unicode_customer"
            assert "args" in tool_call

            # Verify Unicode characters are properly handled
            args = tool_call["args"]
            assert "customer_name" in args
            customer_name = args["customer_name"]

            # The model should include the Unicode characters, not escaped sequences
            assert (
                "你好" in customer_name
                or "你" in customer_name
                or "好" in customer_name
            ), f"Unicode characters not found in: {customer_name}"

        # Test with additional Unicode examples - Japanese
        msgs_jp = [
            HumanMessage(
                "Create a customer named 'こんにちは株式会社' (Hello Corporation) - a "
                "Japanese company"
            )
        ]
        ai_msg_jp = llm_with_tool.invoke(msgs_jp)

        assert isinstance(ai_msg_jp, AIMessage)

        if force_tool_call:
            assert len(ai_msg_jp.tool_calls) >= 1

        if ai_msg_jp.tool_calls:
            tool_call_jp = ai_msg_jp.tool_calls[0]
            args_jp = tool_call_jp["args"]
            customer_name_jp = args_jp["customer_name"]

            # Verify Japanese Unicode characters are preserved
            assert (
                "こんにちは" in customer_name_jp
                or "株式会社" in customer_name_jp
                or "こ" in customer_name_jp
                or "ん" in customer_name_jp
            ), f"Japanese Unicode characters not found in: {customer_name_jp}"