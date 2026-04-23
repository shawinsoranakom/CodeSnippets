async def test_memory_functions_preserve_message_properties(self):
        """Test that memory functions preserve message properties."""
        original_message = Message(
            text="Test with properties",
            sender="User",
            sender_name="Test User",
            flow_id="test_flow",
            session_id="test_session",
            error=False,
            category="message",
        )

        # Test async version
        async_result = await aadd_messages(original_message)
        stored_message = async_result[0]

        assert stored_message.text == original_message.text
        assert stored_message.sender == original_message.sender
        assert stored_message.sender_name == original_message.sender_name
        assert stored_message.flow_id == original_message.flow_id
        assert stored_message.session_id == original_message.session_id
        assert stored_message.error == original_message.error
        assert stored_message.category == original_message.category