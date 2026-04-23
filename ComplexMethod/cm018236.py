async def test_options(
    hass: HomeAssistant,
    entity_type: str,
    extra_options,
    options_options,
) -> None:
    """Test reconfiguring."""

    random_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My random",
            "entity_type": entity_type,
            **extra_options,
        },
        title="My random",
    )
    random_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(random_config_entry.entry_id)
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == entity_type
    assert "name" not in result["data_schema"].schema

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=options_options,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "name": "My random",
        "entity_type": entity_type,
        **options_options,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My random",
        "entity_type": entity_type,
        **options_options,
    }
    assert config_entry.title == "My random"