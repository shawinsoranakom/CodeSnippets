async def test_large_batch_add(self):
        large_batch = [
            Message(
                text=f"Batch {i}",
                sender="User" if i % 2 == 0 else "Machine",
                sender_name="Test User" if i % 2 == 0 else "Bot",
                session_id="large_batch",
            )
            for i in range(50)
        ]
        result = await aadd_messages(large_batch)

        expected_len = 50
        assert len(result) == expected_len
        # Verify sender alternation
        for i, msg in enumerate(result):
            expected_sender = "User" if i % 2 == 0 else "Machine"
            assert msg.sender == expected_sender