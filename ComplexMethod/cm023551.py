async def test_options_flow(hass: HomeAssistant) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_NAME: "test-name",
            CONF_PASSWORD: "test-password",
            CONF_SENSOR_TYPE: "bot",
        },
        options={
            CONF_RETRY_COUNT: 10,
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    with patch_async_setup_entry() as mock_setup_entry:
        entry = await init_integration(hass)

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
    assert result["data"][CONF_RETRY_COUNT] == 3

    assert len(mock_setup_entry.mock_calls) == 2

    # Test changing of entry options.

    with patch_async_setup_entry() as mock_setup_entry:
        entry = await init_integration(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"
        assert result["errors"] is None

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RETRY_COUNT: 6,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_RETRY_COUNT] == 6

    assert len(mock_setup_entry.mock_calls) == 1

    assert entry.options[CONF_RETRY_COUNT] == 6