async def test_generate_content_service(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    store_responses: bool,
    service_data,
    expected_args,
    number_of_files,
) -> None:
    """Test generate content service."""
    conversation_subentry = next(
        sub
        for sub in mock_config_entry.subentries.values()
        if sub.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        conversation_subentry,
        data={**conversation_subentry.data, CONF_STORE_RESPONSES: store_responses},
    )
    await hass.async_block_till_done()

    service_data["config_entry"] = mock_config_entry.entry_id
    expected_args["model"] = "gpt-4o-mini"
    expected_args["max_output_tokens"] = 3000
    expected_args["top_p"] = 1.0
    expected_args["temperature"] = 1.0
    expected_args["user"] = None
    expected_args["store"] = store_responses
    expected_args["input"][0]["type"] = "message"
    expected_args["input"][0]["role"] = "user"

    with (
        patch(
            "openai.resources.responses.AsyncResponses.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch(
            "base64.b64encode", side_effect=[b"BASE64IMAGE1", b"BASE64IMAGE2"]
        ) as mock_b64encode,
        patch("pathlib.Path.read_bytes", Mock(return_value=b"ABC")) as mock_file,
        patch("pathlib.Path.exists", return_value=True),
        patch.object(hass.config, "is_allowed_path", return_value=True),
    ):
        mock_create.return_value = Response(
            object="response",
            id="resp_A",
            created_at=1700000000,
            model="gpt-4o-mini",
            parallel_tool_calls=True,
            tool_choice="auto",
            tools=[],
            output=[
                ResponseOutputMessage(
                    type="message",
                    id="msg_A",
                    content=[
                        ResponseOutputText(
                            type="output_text",
                            text="This is the response",
                            annotations=[],
                        )
                    ],
                    role="assistant",
                    status="completed",
                )
            ],
        )

        response = await hass.services.async_call(
            "openai_conversation",
            "generate_content",
            service_data,
            blocking=True,
            return_response=True,
        )
        assert response == {"text": "This is the response"}
        assert len(mock_create.mock_calls) == 1
        assert mock_create.mock_calls[0][2] == expected_args
        assert mock_b64encode.call_count == number_of_files
        assert mock_file.call_count == number_of_files