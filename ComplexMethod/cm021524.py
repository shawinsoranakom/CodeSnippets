async def test_config_flow_device(
    hass: HomeAssistant,
    template_type: str,
    state_template: dict[str, Any],
    extra_input: dict[str, Any],
    extra_options: dict[str, Any],
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test remove the device registry configuration entry when the device changes."""

    # Configure a device registry
    entry_device = MockConfigEntry()
    entry_device.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry_device.entry_id,
        identifiers={("test", "identifier_test1")},
        connections={("mac", "20:31:32:33:34:01")},
    )
    await hass.async_block_till_done()

    device_id = device.id
    assert device_id is not None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": template_type},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == template_type

    with patch(
        "homeassistant.components.template.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My template",
                "device_id": device_id,
                **state_template,
                **extra_input,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My template"
    assert result["data"] == {}
    assert result["options"] == {
        "name": "My template",
        "template_type": template_type,
        "device_id": device_id,
        **state_template,
        **extra_options,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My template",
        "template_type": template_type,
        "device_id": device_id,
        **state_template,
        **extra_options,
    }