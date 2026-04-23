async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test the reauth flow."""
    hass.config.components.add("google_generative_ai_conversation")
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        state=config_entries.ConfigEntryState.LOADED,
        title="Gemini",
        version=2,
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"
    assert result["context"]["source"] == "reauth"
    assert result["context"]["title_placeholders"] == {"name": "Gemini"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api"
    assert "api_key" in result["data_schema"].schema
    assert not result["errors"]

    with (
        patch(
            "google.genai.models.AsyncModels.list",
        ),
        patch(
            "homeassistant.components.google_generative_ai_conversation.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.google_generative_ai_conversation.async_unload_entry",
            return_value=True,
        ) as mock_unload_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "1234"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert hass.config_entries.async_entries(DOMAIN)[0].data == {"api_key": "1234"}
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1