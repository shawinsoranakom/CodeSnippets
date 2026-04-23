async def test_to_config_basic_agent(self) -> None:
        """Test _to_config method with basic agent configuration."""
        model_client = MagicMock()
        model_client.model_info = {"function_calling": False, "vision": False, "family": ModelFamily.GPT_4O}
        model_client.dump_component = MagicMock(
            return_value=ComponentModel(provider="test", config={"type": "mock_client"})
        )

        mock_context = MagicMock()
        mock_context.dump_component = MagicMock(
            return_value=ComponentModel(provider="test", config={"type": "mock_context"})
        )

        agent = AssistantAgent(
            name="test_agent",
            model_client=model_client,
            description="Test description",
            system_message="Test system message",
            model_context=mock_context,
            metadata={"key": "value"},
        )

        config = agent._to_config()  # type: ignore[reportPrivateUsage]

        assert config.name == "test_agent"
        assert config.description == "Test description"
        assert config.system_message == "Test system message"
        assert config.model_client_stream is False
        assert config.reflect_on_tool_use is False
        assert config.max_tool_iterations == 1
        assert config.metadata == {"key": "value"}
        model_client.dump_component.assert_called_once()
        mock_context.dump_component.assert_called_once()