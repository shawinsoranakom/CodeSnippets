async def test_options_flow_manual_usb_path(
    pyserial_comports: MockFixture, hass: HomeAssistant
) -> None:
    """Test flow with correct login and usb configuration."""
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
            get_mocked_crownstone_cloud(create_mocked_spheres(1))
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USE_USB_OPTION: True}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_config"
    assert pyserial_comports.call_count == 1

    # select manual from the list
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USB_PATH: MANUAL_PATH}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "usb_manual_config"
    assert pyserial_comports.call_count == 2

    # enter USB path
    path = "/dev/crownstone-usb"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_USB_MANUAL_PATH: path}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == create_mocked_entry_options_conf(
        usb_path=path, usb_sphere="sphere_id_0"
    )