async def test_options_configure_rfy_cover_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test we can configure the venetion blind mode of an Rfy cover."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": None,
            "port": None,
            "device": "/dev/tty123",
            "automatic_add": False,
            "devices": {},
        },
        unique_id=DOMAIN,
    )
    result = await start_options_flow(hass, entry)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": True,
            "event_code": "0C1a0000010203010000000000",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "venetian_blind_mode": "EU",
        },
    )

    await hass.async_block_till_done()

    assert (
        entry.data["devices"]["0C1a0000010203010000000000"]["venetian_blind_mode"]
        == "EU"
    )
    assert isinstance(
        entry.data["devices"]["0C1a0000010203010000000000"]["device_id"], list
    )

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    assert device_entries[0].id

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": False,
            "device": device_entries[0].id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "venetian_blind_mode": "EU",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()

    assert (
        entry.data["devices"]["0C1a0000010203010000000000"]["venetian_blind_mode"]
        == "EU"
    )
    assert isinstance(
        entry.data["devices"]["0C1a0000010203010000000000"]["device_id"], list
    )