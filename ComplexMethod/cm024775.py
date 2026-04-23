async def test_discovery_with_existing_device_present(hass: HomeAssistant) -> None:
    """Test setting up discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_ID: "0x000000000099999", CONF_HOST: "4.4.4.4"}
    )
    config_entry.add_to_hass(hass)
    alternate_bulb = _mocked_bulb()
    alternate_bulb.capabilities["id"] = "0x000000000099999"
    alternate_bulb.capabilities["location"] = "yeelight://4.4.4.4"

    with (
        _patch_discovery(),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.AsyncBulb", return_value=alternate_bulb),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(), _patch_discovery_timeout(), _patch_discovery_interval():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    # Now abort and make sure we can start over

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(), _patch_discovery_interval():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.AsyncBulb", return_value=_mocked_bulb()),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE: ID}
        )
        assert result3["type"] is FlowResultType.CREATE_ENTRY
        assert result3["title"] == UNIQUE_FRIENDLY_NAME
        assert result3["data"] == {
            CONF_ID: ID,
            CONF_HOST: IP_ADDRESS,
            CONF_MODEL: MODEL,
        }
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    # ignore configured devices
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(), _patch_discovery_interval():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "no_devices_found"