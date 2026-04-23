async def test_options_flow_remove_usb(hass: HomeAssistant) -> None:
    """Test selecting to set up an USB dongle."""
    configured_entry_data = create_mocked_entry_data_conf(
        email="example@homeassistant.com",
        password="homeassistantisawesome",
    )
    configured_entry_options = create_mocked_entry_options_conf(
        usb_path="/dev/serial/by-id/crownstone-usb",
        usb_sphere="sphere_id_0",
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
            assert schema_key.default()
        if schema_key == CONF_USB_SPHERE_OPTION:
            assert schema_key.default() == "sphere_name_0"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_USE_USB_OPTION: False,
            CONF_USB_SPHERE_OPTION: "sphere_name_0",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == create_mocked_entry_options_conf(
        usb_path=None, usb_sphere=None
    )