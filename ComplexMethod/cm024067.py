async def test_message_history_trimming(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a single message history is trimmed according to the config."""
    response_idx = 0

    def response(*args, **kwargs) -> dict:
        nonlocal response_idx
        response_idx += 1
        return stream_generator(
            {"message": {"role": "assistant", "content": f"response {response_idx}"}}
        )

    with patch(
        "ollama.AsyncClient.chat",
        side_effect=response,
    ) as mock_chat:
        # mock_init_component sets "max_history" to 2
        for i in range(5):
            result = await conversation.async_converse(
                hass,
                f"message {i + 1}",
                conversation_id="1234",
                context=Context(),
                agent_id=mock_config_entry.entry_id,
            )
            assert (
                result.response.response_type == intent.IntentResponseType.ACTION_DONE
            ), result

        assert mock_chat.call_count == 5
        args = mock_chat.call_args_list
        prompt = args[0].kwargs["messages"][0]["content"]

        # system + user-1
        assert len(args[0].kwargs["messages"]) == 2
        assert args[0].kwargs["messages"][1]["content"] == "message 1"

        # Full history
        # system + user-1 + assistant-1 + user-2
        assert len(args[1].kwargs["messages"]) == 4
        assert args[1].kwargs["messages"][0]["role"] == "system"
        assert args[1].kwargs["messages"][0]["content"] == prompt
        assert args[1].kwargs["messages"][1]["role"] == "user"
        assert args[1].kwargs["messages"][1]["content"] == "message 1"
        assert args[1].kwargs["messages"][2]["role"] == "assistant"
        assert args[1].kwargs["messages"][2]["content"] == "response 1"
        assert args[1].kwargs["messages"][3]["role"] == "user"
        assert args[1].kwargs["messages"][3]["content"] == "message 2"

        # Full history
        # system + user-1 + assistant-1 + user-2 + assistant-2 + user-3
        assert len(args[2].kwargs["messages"]) == 6
        assert args[2].kwargs["messages"][0]["role"] == "system"
        assert args[2].kwargs["messages"][0]["content"] == prompt
        assert args[2].kwargs["messages"][1]["role"] == "user"
        assert args[2].kwargs["messages"][1]["content"] == "message 1"
        assert args[2].kwargs["messages"][2]["role"] == "assistant"
        assert args[2].kwargs["messages"][2]["content"] == "response 1"
        assert args[2].kwargs["messages"][3]["role"] == "user"
        assert args[2].kwargs["messages"][3]["content"] == "message 2"
        assert args[2].kwargs["messages"][4]["role"] == "assistant"
        assert args[2].kwargs["messages"][4]["content"] == "response 2"
        assert args[2].kwargs["messages"][5]["role"] == "user"
        assert args[2].kwargs["messages"][5]["content"] == "message 3"

        # Trimmed down to two user messages.
        # system + user-2 + assistant-2 + user-3 + assistant-3 + user-4
        assert len(args[3].kwargs["messages"]) == 6
        assert args[3].kwargs["messages"][0]["role"] == "system"
        assert args[3].kwargs["messages"][0]["content"] == prompt
        assert args[3].kwargs["messages"][1]["role"] == "user"
        assert args[3].kwargs["messages"][1]["content"] == "message 2"
        assert args[3].kwargs["messages"][2]["role"] == "assistant"
        assert args[3].kwargs["messages"][2]["content"] == "response 2"
        assert args[3].kwargs["messages"][3]["role"] == "user"
        assert args[3].kwargs["messages"][3]["content"] == "message 3"
        assert args[3].kwargs["messages"][4]["role"] == "assistant"
        assert args[3].kwargs["messages"][4]["content"] == "response 3"
        assert args[3].kwargs["messages"][5]["role"] == "user"
        assert args[3].kwargs["messages"][5]["content"] == "message 4"

        # Trimmed down to two user messages.
        # system + user-3 + assistant-3 + user-4 + assistant-4 + user-5
        assert len(args[3].kwargs["messages"]) == 6
        assert args[4].kwargs["messages"][0]["role"] == "system"
        assert args[4].kwargs["messages"][0]["content"] == prompt
        assert args[4].kwargs["messages"][1]["role"] == "user"
        assert args[4].kwargs["messages"][1]["content"] == "message 3"
        assert args[4].kwargs["messages"][2]["role"] == "assistant"
        assert args[4].kwargs["messages"][2]["content"] == "response 3"
        assert args[4].kwargs["messages"][3]["role"] == "user"
        assert args[4].kwargs["messages"][3]["content"] == "message 4"
        assert args[4].kwargs["messages"][4]["role"] == "assistant"
        assert args[4].kwargs["messages"][4]["content"] == "response 4"
        assert args[4].kwargs["messages"][5]["role"] == "user"
        assert args[4].kwargs["messages"][5]["content"] == "message 5"