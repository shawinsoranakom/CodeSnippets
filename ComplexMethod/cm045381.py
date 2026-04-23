async def test_config_roundtrip_consistency(self) -> None:
        """Test that converting to config and back preserves agent properties."""
        model_client = MagicMock()
        model_client.model_info = {"function_calling": True, "vision": False, "family": ModelFamily.GPT_4O}
        model_client.dump_component = MagicMock(
            return_value=ComponentModel(provider="test", config={"type": "mock_client"})
        )

        mock_context = MagicMock()
        mock_context.dump_component = MagicMock(
            return_value=ComponentModel(provider="test", config={"type": "mock_context"})
        )

        original_agent = AssistantAgent(
            name="test_agent",
            model_client=model_client,
            description="Test description",
            system_message="Test system message",
            model_client_stream=True,
            reflect_on_tool_use=True,
            max_tool_iterations=5,
            tool_call_summary_format="{tool_name}: {result}",
            handoffs=["agent1"],
            model_context=mock_context,
            metadata={"test": "value"},
        )

        # Convert to config
        config = original_agent._to_config()  # type: ignore[reportPrivateUsage]

        # Verify config properties
        assert config.name == "test_agent"
        assert config.description == "Test description"
        assert config.system_message == "Test system message"
        assert config.model_client_stream is True
        assert config.reflect_on_tool_use is True
        assert config.max_tool_iterations == 5
        assert config.tool_call_summary_format == "{tool_name}: {result}"
        assert config.metadata == {"test": "value"}