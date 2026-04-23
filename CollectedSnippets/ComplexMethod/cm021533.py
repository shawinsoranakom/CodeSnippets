async def test_options_flow_change_device(
    hass: HomeAssistant,
    template_type: str,
    state_template: dict[str, Any],
    extra_input: dict[str, Any],
    extra_options: dict[str, Any],
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test remove the device registry configuration entry when the device changes."""

    # Configure a device registry
    entry_device1 = MockConfigEntry()
    entry_device1.add_to_hass(hass)
    device1 = device_registry.async_get_or_create(
        config_entry_id=entry_device1.entry_id,
        identifiers={("test", "identifier_test1")},
        connections={("mac", "20:31:32:33:34:01")},
    )
    entry_device2 = MockConfigEntry()
    entry_device2.add_to_hass(hass)
    device2 = device_registry.async_get_or_create(
        config_entry_id=entry_device1.entry_id,
        identifiers={("test", "identifier_test2")},
        connections={("mac", "20:31:32:33:34:02")},
    )
    await hass.async_block_till_done()

    device_id1 = device1.id
    assert device_id1 is not None

    device_id2 = device2.id
    assert device_id2 is not None

    # Setup the config entry with device 1
    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "template_type": template_type,
            "name": "My template",
            "device_id": device_id1,
            **state_template,
            **extra_options,
        },
        title="Template",
    )
    template_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(template_config_entry.entry_id)
    await hass.async_block_till_done()

    # Change to link to device 2
    result = await hass.config_entries.options.async_init(
        template_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "device_id": device_id2,
            **state_template,
            **extra_input,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "template_type": template_type,
        "name": "My template",
        "device_id": device_id2,
        **state_template,
        **extra_input,
    }
    assert template_config_entry.data == {}
    assert template_config_entry.options == {
        "template_type": template_type,
        "name": "My template",
        "device_id": device_id2,
        **state_template,
        **extra_options,
    }

    # Remove link with device
    result = await hass.config_entries.options.async_init(
        template_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            **state_template,
            **extra_input,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "template_type": template_type,
        "name": "My template",
        **state_template,
        **extra_input,
    }
    assert template_config_entry.data == {}
    assert template_config_entry.options == {
        "template_type": template_type,
        "name": "My template",
        **state_template,
        **extra_options,
    }

    # Change to link to device 1
    result = await hass.config_entries.options.async_init(
        template_config_entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "device_id": device_id1,
            **state_template,
            **extra_input,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "template_type": template_type,
        "name": "My template",
        "device_id": device_id1,
        **state_template,
        **extra_input,
    }
    assert template_config_entry.data == {}
    assert template_config_entry.options == {
        "template_type": template_type,
        "name": "My template",
        "device_id": device_id1,
        **state_template,
        **extra_options,
    }