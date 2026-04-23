async def test_discovery_with_existing_device_present(hass: HomeAssistant) -> None:
    """Test setting up discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.2"}, unique_id="dd:dd:dd:dd:dd:dd"
    )
    config_entry.add_to_hass(hass)

    with (
        _patch_device(),
        _patch_discovery(),
        _patch_config_flow_try_connect(no_device=True),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(), _patch_config_flow_try_connect():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
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

    with _patch_discovery(), _patch_config_flow_try_connect():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    with (
        _patch_discovery(),
        _patch_config_flow_try_connect(),
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE: SERIAL}
        )
        assert result3["type"] is FlowResultType.CREATE_ENTRY
        assert result3["title"] == DEFAULT_ENTRY_TITLE
        assert result3["data"] == {
            CONF_HOST: IP_ADDRESS,
        }
        await hass.async_block_till_done()

    mock_setup_entry.assert_called_once()

    # ignore configured devices
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery(), _patch_config_flow_try_connect():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "no_devices_found"