async def test_invalid_model(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_init_component: None
) -> None:
    """Test exceptions during fetching model info."""
    options = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )

    # Configure initial step
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {
            CONF_NAME: "Mock name",
            **DEFAULT_CONVERSATION_OPTIONS,
            CONF_RECOMMENDED: False,
        },
    )
    assert options["type"] is FlowResultType.FORM
    assert options["step_id"] == "advanced"

    # Configure advanced step but with api error
    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.retrieve",
        new_callable=AsyncMock,
        side_effect=InternalServerError(
            message="Mock server error",
            response=Response(
                status_code=500,
                request=Request(method="POST", url=URL()),
            ),
            body=None,
        ),
    ):
        options = await hass.config_entries.subentries.async_configure(
            options["flow_id"],
            {
                CONF_CHAT_MODEL: "invalid-model-2-0",
            },
        )
    assert options["type"] is FlowResultType.FORM
    assert options["errors"] == {"chat_model": "api_error"}
    assert options["description_placeholders"] == {"message": "Mock server error"}

    # Try again
    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.retrieve",
        new_callable=AsyncMock,
        side_effect=NotFoundError(
            message="Model not found",
            response=Response(
                status_code=404,
                request=Request(method="GET", url=URL()),
            ),
            body={
                "type": "error",
                "error": {
                    "type": "not_found_error",
                    "message": "model: invalid-model-2-0",
                },
            },
        ),
    ):
        options = await hass.config_entries.subentries.async_configure(
            options["flow_id"],
            {
                CONF_CHAT_MODEL: "invalid-model-2-0",
            },
        )
    assert options["type"] is FlowResultType.FORM
    assert options["errors"] == {"chat_model": "model_not_found"}

    # Try again with a valid model
    with patch(
        "homeassistant.components.anthropic.config_flow.anthropic.resources.models.AsyncModels.retrieve",
        new_callable=AsyncMock,
        return_value=ModelInfo(
            type="model",
            id="valid-model-4-5",
            created_at=datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC),
            display_name="Valid Model 4-5",
        ),
    ):
        options = await hass.config_entries.subentries.async_configure(
            options["flow_id"],
            {
                CONF_CHAT_MODEL: "valid-model-4-5",
            },
        )

    assert options["type"] is FlowResultType.FORM
    assert not options["errors"]
    assert options["step_id"] == "model"

    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {},
    )

    assert options["type"] is FlowResultType.CREATE_ENTRY
    assert options["data"][CONF_CHAT_MODEL] == "valid-model-4-5"