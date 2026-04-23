async def test_successful_login_with_manual_usb_path(
    crownstone_setup: MockFixture, pyserial_comports: MockFixture, hass: HomeAssistant
) -> None:
    """Test flow with correct login and usb configuration."""
    entry_data_with_manual_usb = create_mocked_entry_data_conf(
        email="example@homeassistant.com",
        password="homeassistantisawesome",
    )
    entry_options_with_manual_usb = create_mocked_entry_options_conf(
        usb_path="/dev/crownstone-usb",
        usb_sphere="sphere_id_0",
    )

    result = await start_config_flow(
        hass, get_mocked_crownstone_cloud(create_mocked_spheres(1))
    )
    # should show usb form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_config"
    assert pyserial_comports.call_count == 1

    # select manual from the list
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_USB_PATH: MANUAL_PATH}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_manual_config"
    assert pyserial_comports.call_count == 2

    # enter USB path
    path = "/dev/crownstone-usb"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_USB_MANUAL_PATH: path}
    )

    # since we only have 1 sphere here, test that it's automatically selected and
    # creating entry without asking for user input
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == entry_data_with_manual_usb
    assert result["options"] == entry_options_with_manual_usb
    assert crownstone_setup.call_count == 1