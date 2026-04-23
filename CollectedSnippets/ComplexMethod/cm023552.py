async def test_options_flow_lock_pro(hass: HomeAssistant) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_NAME: "test-name",
            CONF_PASSWORD: "test-password",
            CONF_SENSOR_TYPE: "lock_pro",
        },
        options={CONF_RETRY_COUNT: 10},
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    # Test Force night_latch should be disabled by default.
    with patch_async_setup_entry() as mock_setup_entry:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"
        assert result["errors"] is None

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RETRY_COUNT: 3,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LOCK_NIGHTLATCH] is False

    assert len(mock_setup_entry.mock_calls) == 1

    # Test Set force night_latch to be enabled.

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"
        assert result["errors"] is None

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCK_NIGHTLATCH: True,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LOCK_NIGHTLATCH] is True

    assert len(mock_setup_entry.mock_calls) == 0

    assert entry.options[CONF_LOCK_NIGHTLATCH] is True