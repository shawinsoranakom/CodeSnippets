async def test_option_flow_led_settings(
    hass: HomeAssistant,
    set_yellow_settings: AsyncMock,
    reboot_host: AsyncMock,
    reboot_menu_choice: str,
    reboot_calls: int,
) -> None:
    """Test updating LED settings."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={"firmware": ApplicationType.EZSP},
        domain=DOMAIN,
        options={},
        title="Home Assistant Yellow",
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "main_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "hardware_settings"},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"disk_led": False, "heartbeat_led": False, "power_led": False},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reboot_menu"
    set_yellow_settings.assert_called_once_with(
        YellowOptions(disk_led=False, heartbeat_led=False, power_led=False)
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": reboot_menu_choice},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert reboot_host.call_count == reboot_calls