async def test_reauth_flow_errors(hass: HomeAssistant, side_effect, error) -> None:
    """Test reauthentication flow when authentication fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://localhost:11434",
            CONF_API_KEY: "old-api-key",
        },
        version=3,
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "other-api-key",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": error}

    with patch(
        "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
        return_value={"models": [{"model": TEST_MODEL}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "new-api-key",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert entry.data == {
        CONF_URL: "http://localhost:11434",
        CONF_API_KEY: "new-api-key",
    }