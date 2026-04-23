async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=WOCURTAIN_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[WOCURTAIN_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
        assert result["type"] is FlowResultType.FORM

    with patch_async_setup_entry() as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Curtain EEFF"
    assert result2["data"] == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_SENSOR_TYPE: "curtain",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)