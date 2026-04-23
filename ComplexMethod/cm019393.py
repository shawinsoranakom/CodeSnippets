async def test_successful_login_with_usb(
    crownstone_setup: MockFixture,
    pyserial_comports_none_types: MockFixture,
    hass: HomeAssistant,
) -> None:
    """Test flow with correct login and usb configuration."""
    entry_data_with_usb = create_mocked_entry_data_conf(
        email="example@homeassistant.com",
        password="homeassistantisawesome",
    )
    entry_options_with_usb = create_mocked_entry_options_conf(
        usb_path="/dev/ttyUSB1234",
        usb_sphere="sphere_id_1",
    )

    result = await start_config_flow(
        hass, get_mocked_crownstone_cloud(create_mocked_spheres(2))
    )
    # should show usb form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_config"
    assert pyserial_comports_none_types.call_count == 1

    # create a mocked port which should be in
    # the list returned from list_ports_as_str, from .helpers
    port = get_mocked_com_port_none_types()
    port_select = usb.human_readable_device_name(
        port.device,
        port.serial_number,
        port.manufacturer,
        port.description,
        port.vid,
        port.pid,
    )

    # select a port from the list
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_USB_PATH: port_select}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_sphere_config"
    assert pyserial_comports_none_types.call_count == 2

    # select a sphere
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_USB_SPHERE: "sphere_name_1"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == entry_data_with_usb
    assert result["options"] == entry_options_with_usb
    assert crownstone_setup.call_count == 1