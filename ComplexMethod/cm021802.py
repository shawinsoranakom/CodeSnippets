async def test_options_form(
    hass: HomeAssistant,
    mock_pyotgw: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the options form."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Mock Gateway",
        data={
            CONF_NAME: "Mock Gateway",
            CONF_DEVICE: "/dev/null",
            CONF_ID: "mock_gateway",
        },
        options={},
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )
    assert flow["type"] is FlowResultType.FORM
    assert flow["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_FLOOR_TEMP: True,
            CONF_READ_PRECISION: PRECISION_HALVES,
            CONF_SET_PRECISION: PRECISION_HALVES,
            CONF_TEMPORARY_OVRD_MODE: True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_READ_PRECISION] == PRECISION_HALVES
    assert result["data"][CONF_SET_PRECISION] == PRECISION_HALVES
    assert result["data"][CONF_TEMPORARY_OVRD_MODE] is True
    assert result["data"][CONF_FLOOR_TEMP] is True

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={CONF_READ_PRECISION: 0}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_READ_PRECISION] == 0.0
    assert result["data"][CONF_SET_PRECISION] == PRECISION_HALVES
    assert result["data"][CONF_TEMPORARY_OVRD_MODE] is True
    assert result["data"][CONF_FLOOR_TEMP] is True

    flow = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )

    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_FLOOR_TEMP: False,
            CONF_READ_PRECISION: PRECISION_TENTHS,
            CONF_SET_PRECISION: PRECISION_HALVES,
            CONF_TEMPORARY_OVRD_MODE: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_READ_PRECISION] == PRECISION_TENTHS
    assert result["data"][CONF_SET_PRECISION] == PRECISION_HALVES
    assert result["data"][CONF_TEMPORARY_OVRD_MODE] is False
    assert result["data"][CONF_FLOOR_TEMP] is False