async def test_options_flow_setup_usb(
    pyserial_comports: MockFixture, hass: HomeAssistant
) -> None:
    """Test options flow init."""
    configured_entry_data = create_mocked_entry_data_conf(
        email="example@homeassistant.com",
        password="homeassistantisawesome",
    )
    configured_entry_options = create_mocked_entry_options_conf(
        usb_path=None,
        usb_sphere=None,
    )

    # create mocked entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=configured_entry_data,
        options=configured_entry_options,
        unique_id="account_id",
    )
    entry.add_to_hass(hass)

    result = await start_options_flow(
        hass,
        entry,
        get_mocked_crownstone_entry_manager(
            get_mocked_crownstone_cloud(create_mocked_spheres(2))
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    schema = result["data_schema"].schema
    for schema_key in schema:
        if schema_key == CONF_USE_USB_OPTION:
            assert not schema_key.default()

    # USB is not set up, so this should not be in the options
    assert CONF_USB_SPHERE_OPTION not in schema

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USE_USB_OPTION: True}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_config"
    assert pyserial_comports.call_count == 1

    # create a mocked port which should be in
    # the list returned from list_ports_as_str, from .helpers
    port = get_mocked_com_port()
    port_select = usb.human_readable_device_name(
        port.device,
        port.serial_number,
        port.manufacturer,
        port.description,
        port.vid,
        port.pid,
    )

    # select a port from the list
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USB_PATH: port_select}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_sphere_config"
    assert pyserial_comports.call_count == 2

    # select a sphere
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USB_SPHERE: "sphere_name_1"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == create_mocked_entry_options_conf(
        usb_path="/dev/ttyUSB1234", usb_sphere="sphere_id_1"
    )