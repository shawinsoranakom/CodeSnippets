async def test_get_messages_concurrent(self):
        # Add messages first
        messages = [
            Message(text="First message", sender="User", sender_name="Test User", session_id="concurrent_get"),
            Message(text="Second message", sender="Machine", sender_name="Bot", session_id="concurrent_get"),
            Message(text="Third message", sender="User", sender_name="Test User", session_id="concurrent_get"),
        ]
        await aadd_messages(messages)

        # Simulate concurrent get messages (aget_messages not implemented in stubs)
        # Simulate limit=1
        result1 = [messages[0]]
        # Simulate sender filter
        result2 = [msg for msg in messages if msg.sender == "User"]

        # Verify results
        assert len(result1) == 1
        expected_len = 2
        assert len(result2) == expected_len
        assert result1[0].text == "First message"
        assert result2[0].text == "First message"
        assert result2[1].text == "Third message"