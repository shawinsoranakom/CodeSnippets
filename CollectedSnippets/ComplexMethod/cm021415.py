async def test_user_setup(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_bridge: MagicMock
) -> None:
    """Test we can finish a config flow."""
    with patch("homeassistant.components.switcher_kis.utils.DISCOVERY_TIME_SEC", 0):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "confirm"

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        assert mock_bridge.is_running is False
        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert result2["title"] == "Switcher"
        assert result2["result"].data == {CONF_USERNAME: None, CONF_TOKEN: None}

        await hass.async_block_till_done()

        assert len(mock_setup_entry.mock_calls) == 1