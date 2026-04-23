async def test_mock_serialization_api_key() -> None:
    client = AnthropicChatCompletionClient(
        model="claude-3-haiku-20240307",  # Use haiku for faster/cheaper testing
        api_key="sk-password",
        temperature=0.0,  # Added temperature param to test
        stop_sequences=["STOP"],  # Added stop sequence
    )
    assert client
    config = client.dump_component()
    assert config
    assert "sk-password" not in str(config)
    serialized_config = config.model_dump_json()
    assert serialized_config
    assert "sk-password" not in serialized_config
    client2 = AnthropicChatCompletionClient.load_component(config)
    assert client2

    bedrock_client = AnthropicBedrockChatCompletionClient(
        model="claude-3-haiku-20240307",  # Use haiku for faster/cheaper testing
        api_key="sk-password",
        model_info=ModelInfo(
            vision=False, function_calling=True, json_output=False, family="unknown", structured_output=True
        ),
        bedrock_info=BedrockInfo(
            aws_access_key="<aws_access_key>",
            aws_secret_key="<aws_secret_key>",
            aws_session_token="<aws_session_token>",
            aws_region="<aws_region>",
        ),
    )
    assert bedrock_client
    bedrock_config = bedrock_client.dump_component()
    assert bedrock_config
    assert "sk-password" not in str(bedrock_config)
    serialized_bedrock_config = bedrock_config.model_dump_json()
    assert serialized_bedrock_config
    assert "sk-password" not in serialized_bedrock_config
    bedrock_client2 = AnthropicBedrockChatCompletionClient.load_component(bedrock_config)
    assert bedrock_client2