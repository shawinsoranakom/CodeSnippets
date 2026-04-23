async def test_options_flow_curtain_speed(hass: HomeAssistant) -> None:
    """Test updating curtain speed option."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_NAME: "test-name",
            CONF_SENSOR_TYPE: "curtain",
        },
        options={CONF_RETRY_COUNT: 2, CONF_CURTAIN_SPEED: 255},
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

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
                CONF_RETRY_COUNT: 4,
                CONF_CURTAIN_SPEED: 100,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_RETRY_COUNT] == 4
    assert result["data"][CONF_CURTAIN_SPEED] == 100
    assert entry.options[CONF_CURTAIN_SPEED] == 100
    assert len(mock_setup_entry.mock_calls) == 1