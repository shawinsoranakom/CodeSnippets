async def test_config_flow(hass: HomeAssistant) -> None:
    """Test the config flow."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    with (
        patch(
            "homeassistant.components.homeassistant_yellow.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.homeassistant_hardware.firmware_config_flow.probe_silabs_firmware_info",
            return_value=FirmwareInfo(
                device=RADIO_DEVICE,
                firmware_type=ApplicationType.EZSP,
                firmware_version=None,
                owners=[],
                source="probe",
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home Assistant Yellow"
    assert result["data"] == {"firmware": "ezsp", "firmware_version": None}
    assert result["options"] == {}
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {"firmware": "ezsp", "firmware_version": None}
    assert config_entry.options == {}
    assert config_entry.title == "Home Assistant Yellow"