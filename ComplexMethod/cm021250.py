async def test_full_user_flow(
    hass: HomeAssistant,
    mock_tailscale_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-FAKE",
        },
    )

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "homeassistant.github"
    assert result2.get("data") == {
        CONF_TAILNET: "homeassistant.github",
        CONF_API_KEY: "tskey-FAKE",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_tailscale_config_flow.devices.mock_calls) == 1