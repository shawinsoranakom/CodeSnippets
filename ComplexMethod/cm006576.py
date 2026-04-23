async def test_large_batch_message_processing(self):
        """Test processing a large batch of messages."""
        # Create a larger batch to test performance
        large_batch = [
            Message(
                text=f"Batch message {i}",
                sender="User" if i % 2 == 0 else "AI",
                sender_name="Test User" if i % 2 == 0 else "Assistant",
                session_id="test-large-batch",
            )
            for i in range(50)
        ]

        result = await aadd_messages(large_batch)

        assert len(result) == 50
        # Verify sender alternation
        for i, msg in enumerate(result):
            expected_sender = "User" if i % 2 == 0 else "AI"
            assert msg.sender == expected_sender
            assert msg.text == f"Batch message {i}"