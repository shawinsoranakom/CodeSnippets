def test_message_to_dict_conversion_preserves_order(self):
        """Test that BaseMessage to dict conversion preserves order.

        This tests the specific conversion that happens in ValidatedTool._validate_and_run()
        where BaseMessages get converted to dicts for SPARC.
        """
        from langchain_core.messages.base import message_to_dict
        from lfx.schema.data import Data

        # Create test data in chronological order
        message1 = Data(data={"text": "first message", "sender": "User"})
        message2 = Data(data={"text": "second message", "sender": "Assistant"})
        message3 = Data(data={"text": "third message", "sender": "User"})

        # Convert to BaseMessages (as build_conversation_context does)
        base_messages = []
        for msg_data in [message1, message2, message3]:
            base_msg = msg_data.to_lc_message()
            base_messages.append(base_msg)

        # Convert to dicts (as ValidatedTool does for SPARC)
        dict_messages = [message_to_dict(msg) for msg in base_messages]

        logger.debug("\n=== MESSAGE CONVERSION DEBUG ===")
        for i, (base_msg, dict_msg) in enumerate(zip(base_messages, dict_messages, strict=False)):
            logger.debug(f"{i}: Base: {base_msg.content}")
            logger.debug(f"   Dict: {dict_msg.get('data', {}).get('content', 'NO_CONTENT')}")
        logger.debug("===============================\n")

        # Verify the conversion preserves order
        assert len(dict_messages) == 3

        # Check that first message content is preserved
        first_content = dict_messages[0].get("data", {}).get("content")
        assert "first message" in str(first_content), f"First message not preserved: {first_content}"

        # Check that last message content is preserved
        last_content = dict_messages[2].get("data", {}).get("content")
        assert "third message" in str(last_content), f"Last message not preserved: {last_content}"

        # The order should be: first, second, third
        contents = []
        for dict_msg in dict_messages:
            content = dict_msg.get("data", {}).get("content")
            if isinstance(content, list):
                # Handle User message format
                text_content = next(
                    (item.get("text") for item in content if item.get("type") == "text"),
                    "",
                )
                contents.append(text_content)
            else:
                # Handle AI message format
                contents.append(str(content))

        logger.debug(f"Extracted contents: {contents}")

        # Verify chronological order is maintained
        assert "first" in contents[0], f"First position wrong: {contents[0]}"
        assert "second" in contents[1], f"Second position wrong: {contents[1]}"
        assert "third" in contents[2], f"Third position wrong: {contents[2]}"