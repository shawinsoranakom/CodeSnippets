async def test_reasoning_effort_parameter() -> None:
    """Test that reasoning_effort parameter is properly handled in client configuration."""

    # Test OpenAI client with reasoning_effort
    openai_client = OpenAIChatCompletionClient(
        model="gpt-5",
        api_key="fake_key",
        reasoning_effort="low",
    )
    assert openai_client._create_args["reasoning_effort"] == "low"  # pyright: ignore[reportPrivateUsage]

    # Test Azure OpenAI client with reasoning_effort
    azure_client = AzureOpenAIChatCompletionClient(
        model="gpt-5",
        azure_endpoint="fake_endpoint",
        azure_deployment="gpt-5-2025-08-07",
        api_version="2025-02-01-preview",
        api_key="fake_key",
        reasoning_effort="medium",
    )
    assert azure_client._create_args["reasoning_effort"] == "medium"  # pyright: ignore[reportPrivateUsage]

    # Test load_component with reasoning_effort for OpenAI
    from autogen_core.models import ChatCompletionClient

    openai_config = {
        "provider": "OpenAIChatCompletionClient",
        "config": {
            "model": "gpt-5",
            "api_key": "fake_key",
            "reasoning_effort": "high",
        },
    }

    loaded_openai_client = ChatCompletionClient.load_component(openai_config)
    assert loaded_openai_client._create_args["reasoning_effort"] == "high"  # type: ignore[attr-defined] # pyright: ignore[reportPrivateUsage, reportUnknownMemberType, reportAttributeAccessIssue]
    assert loaded_openai_client._raw_config["reasoning_effort"] == "high"  # type: ignore[attr-defined] # pyright: ignore[reportPrivateUsage, reportUnknownMemberType, reportAttributeAccessIssue]

    # Test load_component with reasoning_effort for Azure OpenAI
    azure_config = {
        "provider": "AzureOpenAIChatCompletionClient",
        "config": {
            "model": "gpt-5",
            "azure_endpoint": "fake_endpoint",
            "azure_deployment": "gpt-5-2025-08-07",
            "api_version": "2025-02-01-preview",
            "api_key": "fake_key",
            "reasoning_effort": "low",
        },
    }

    loaded_azure_client = ChatCompletionClient.load_component(azure_config)
    assert loaded_azure_client._create_args["reasoning_effort"] == "low"  # type: ignore[attr-defined] # pyright: ignore[reportPrivateUsage, reportUnknownMemberType, reportAttributeAccessIssue]
    assert loaded_azure_client._raw_config["reasoning_effort"] == "low"  # type: ignore[attr-defined] # pyright: ignore[reportPrivateUsage, reportUnknownMemberType, reportAttributeAccessIssue]

    # Test serialization and deserialization
    config_dict = openai_client.dump_component()
    reloaded_client = OpenAIChatCompletionClient.load_component(config_dict)
    assert reloaded_client._create_args["reasoning_effort"] == "low"