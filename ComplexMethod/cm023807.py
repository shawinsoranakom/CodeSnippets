async def test_discovery_with_firmware_update(hass: HomeAssistant) -> None:
    """Test we check the device again between first discovery and config entry creation."""
    with _patch_wizlight(
        device=None,
        extended_white_range=FAKE_EXTENDED_WHITE_RANGE,
        bulb_type=FAKE_RGBW_BULB,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=INTEGRATION_DISCOVERY,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    # In between discovery and when the user clicks to set it up the firmware
    # updates and we now can see its really RGBWW not RGBW since the older
    # firmwares did not tell us how many white channels exist

    with (
        patch(
            "homeassistant.components.wiz.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.wiz.async_setup", return_value=True
        ) as mock_setup,
        _patch_wizlight(
            device=None,
            extended_white_range=FAKE_EXTENDED_WHITE_RANGE,
            bulb_type=FAKE_RGBWW_BULB,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "WiZ RGBWW Tunable ABCABC"
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1