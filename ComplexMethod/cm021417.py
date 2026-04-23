async def test_user_setup_found_token_device_invalid_token(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we can finish a config flow with token device found."""
    with patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "credentials"

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=False,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "invalid_auth"}

    with patch(
        "homeassistant.components.switcher_kis.config_flow.validate_token",
        return_value=True,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_USERNAME: DUMMY_USERNAME, CONF_TOKEN: DUMMY_TOKEN},
        )

        assert result4["type"] is FlowResultType.CREATE_ENTRY
        assert result4["title"] == "Switcher"
        assert result4["result"].data == {
            CONF_USERNAME: DUMMY_USERNAME,
            CONF_TOKEN: DUMMY_TOKEN,
        }

    assert len(mock_setup_entry.mock_calls) == 1