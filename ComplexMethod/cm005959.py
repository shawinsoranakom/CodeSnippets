def test_conversation_context_chronological_order(self):
        """Test that conversation context maintains chronological order.

        Reproduces the bug where conversation context appears reversed:
        Expected: [oldest_message, ..., newest_message]
        Actual: [newest_message, ..., oldest_message]
        """
        from lfx.schema.data import Data

        # Create a conversation with clear chronological order
        message1 = Data(data={"text": "how much is 353454 345454", "sender": "User"})
        message2 = Data(
            data={
                "text": "It seems there was some confusion regarding the operation...",
                "sender": "Assistant",
            }
        )
        message3 = Data(data={"text": "I wanted to write there plus", "sender": "User"})

        agent = ALTKAgentComponent(
            _type="Agent",
            agent_llm=MockLanguageModel(),
            input_value="test current query",
            tools=[MockTool()],
            chat_history=[message1, message2, message3],  # Chronological order
        )

        # Get the conversation context as built by ALTKBaseAgentComponent
        context = agent.build_conversation_context()

        # Log the context for debugging
        logger.debug("\n=== CONVERSATION CONTEXT DEBUG ===")
        for i, msg in enumerate(context):
            logger.debug(f"{i}: {type(msg).__name__} - {msg.content}")
        logger.debug("===================================\n")

        # Expected chronological order (after input_value):
        # 0: input_value ("test current query")
        # 1: message1 ("how much is 353454 345454")
        # 2: message2 ("It seems there was some confusion...")
        # 3: message3 ("I wanted to write there plus")

        assert len(context) == 4  # input + 3 chat history messages

        # Check if messages are in chronological order
        # Extract text content using our normalize function
        from lfx.base.agents.altk_base_agent import normalize_message_content

        msg_texts = [normalize_message_content(msg) for msg in context]

        # Expected order
        expected_texts = [
            "how much is 353454 345454",  # First message
            "It seems there was some confusion regarding the operation...",  # Agent response
            "I wanted to write there plus",  # Latest message
            "test current query",  # Input value
        ]

        logger.debug(f"Expected: {expected_texts}")
        logger.debug(f"Actual:   {msg_texts}")

        # Check each message position
        assert "test current query" in msg_texts[-1], "Input should be first"

        # Find the positions of our test messages
        msg1_pos = next((i for i, text in enumerate(msg_texts) if "353454 345454" in text), None)
        msg2_pos = next(
            (i for i, text in enumerate(msg_texts) if "confusion regarding" in text),
            None,
        )
        msg3_pos = next((i for i, text in enumerate(msg_texts) if "write there plus" in text), None)

        logger.debug(f"Message positions - msg1: {msg1_pos}, msg2: {msg2_pos}, msg3: {msg3_pos}")

        # Verify chronological order
        assert msg1_pos is not None, "First message should be present"
        assert msg2_pos is not None, "Second message should be present"
        assert msg3_pos is not None, "Third message should be present"

        # This assertion will likely FAIL and expose the bug
        assert msg1_pos < msg2_pos < msg3_pos, (
            f"Messages should be in chronological order, but got positions: {msg1_pos} < {msg2_pos} < {msg3_pos}"
        )