async def test_reconfigure_preserves_existing_config_entry_fields(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure only updates changed fields and preserves existing config entry data."""
    # Simulate a config entry imported from yaml with extra fields
    initial_data = {
        CONF_HOST: "elks://1.2.3.4",
        CONF_USERNAME: "olduser",
        CONF_PASSWORD: "oldpass",
        CONF_PREFIX: "oldprefix",
        CONF_AUTO_CONFIGURE: False,
        "extra_field": "should_be_preserved",
        "another_field": 42,
    }
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=initial_data,
        unique_id=MOCK_MAC,
    )
    config_entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await config_entry.start_reconfigure_flow(hass)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)
    with (
        _patch_discovery(no_device=True),
        _patch_elk(mocked_elk),
        patch("homeassistant.components.elkm1.async_setup_entry", return_value=True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "newuser",
                CONF_PASSWORD: "newpass",
                CONF_ADDRESS: "5.6.7.8",
                CONF_PROTOCOL: "secure",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"

    await hass.async_block_till_done()
    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    assert updated_entry is not None
    assert updated_entry.data[CONF_HOST] == "elks://5.6.7.8"
    assert updated_entry.data[CONF_USERNAME] == "newuser"
    assert updated_entry.data[CONF_PASSWORD] == "newpass"
    assert updated_entry.data[CONF_AUTO_CONFIGURE] is False
    assert updated_entry.data[CONF_PREFIX] == "oldprefix"
    assert updated_entry.data["extra_field"] == "should_be_preserved"
    assert updated_entry.data["another_field"] == 42