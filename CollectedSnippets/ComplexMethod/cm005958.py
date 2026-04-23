def test_altk_agent_handles_inconsistent_message_content(self):
        """Test that ALTK agent correctly handles inconsistent Data.to_lc_message() formats."""
        from lfx.schema.data import Data

        # Test with User data (produces list content format)
        user_data = Data(data={"text": "test user query", "sender": "User"})

        agent = ALTKAgentComponent(
            _type="Agent",
            agent_llm=MockLanguageModel(),
            input_value=user_data,  # This will call Data.to_lc_message() internally
            tools=[],
        )

        # Test that get_user_query works with the Data input
        user_query = agent.get_user_query()
        assert user_query == "test user query"  # Data.get_text() should be called

        # Test with Assistant data (produces string content format)
        assistant_data = Data(data={"text": "test assistant message", "sender": "Assistant"})

        agent.input_value = assistant_data
        assistant_query = agent.get_user_query()
        assert assistant_query == "test assistant message"  # Data.get_text() should be called

        # Both should be handled consistently
        assert isinstance(user_query, str)
        assert isinstance(assistant_query, str)

        # Test build_conversation_context with mixed data types
        agent.input_value = "simple string"
        agent.chat_history = [user_data, assistant_data]  # Mixed content formats

        context = agent.build_conversation_context()
        assert len(context) == 3  # input + 2 history items

        # All should be BaseMessage instances
        from langchain_core.messages import BaseMessage

        for msg in context:
            assert isinstance(msg, BaseMessage)
            # Content should be accessible (even if format differs)
            assert hasattr(msg, "content")
            assert msg.content is not None