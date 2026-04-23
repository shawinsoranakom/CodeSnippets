async def test_config_flow(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    pvpc_aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test config flow for pvpc_hourly_pricing.

    - Create a new entry with tariff "2.0TD (Ceuta/Melilla)"
    - Check state and attributes
    - Check abort when trying to config another with same tariff
    - Check removal and add again to check state restoration
    - Configure options to introduce API Token, with bad auth and good one
    """
    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    await hass.config.async_set_time_zone("Europe/Madrid")
    tst_config = {
        CONF_NAME: "test",
        ATTR_TARIFF: TARIFFS[1],
        ATTR_POWER: 4.6,
        ATTR_POWER_P3: 5.75,
        CONF_USE_API_TOKEN: False,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    assert pvpc_aioclient_mock.call_count == 1

    # no extra sensors created without enabled API token
    state_inyection = hass.states.get("sensor.injection_price")
    assert state_inyection is None

    # Check abort when configuring another with same tariff
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    assert result["type"] is FlowResultType.ABORT
    assert pvpc_aioclient_mock.call_count == 1

    # Check removal
    registry_entity = entity_registry.async_get("sensor.esios_pvpc")
    assert await hass.config_entries.async_remove(registry_entity.config_entry_id)

    # and add it again with UI
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    assert pvpc_aioclient_mock.call_count == 2
    assert state.attributes["period"] == "P3"
    assert state.attributes["next_period"] == "P2"
    assert state.attributes["available_power"] == 5750

    # check options flow
    current_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(current_entries) == 1
    config_entry = current_entries[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={ATTR_POWER: 3.0, ATTR_POWER_P3: 4.6, CONF_USE_API_TOKEN: True},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_token"
    assert pvpc_aioclient_mock.call_count == 2
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    assert pvpc_aioclient_mock.call_count == 3
    assert state.attributes["period"] == "P3"
    assert state.attributes["next_period"] == "P2"
    assert state.attributes["available_power"] == 4600

    state_inyection = hass.states.get("sensor.esios_injection_price")
    state_mag = hass.states.get("sensor.esios_mag_tax")
    state_omie = hass.states.get("sensor.esios_omie_price")
    assert state_inyection
    assert not state_mag
    assert not state_omie
    assert "period" not in state_inyection.attributes
    assert "available_power" not in state_inyection.attributes

    # check update failed
    freezer.tick(timedelta(days=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[0], value="unavailable")
    assert "period" not in state.attributes
    assert pvpc_aioclient_mock.call_count == 5

    # disable api token in options
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={ATTR_POWER: 3.0, ATTR_POWER_P3: 4.6, CONF_USE_API_TOKEN: False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert pvpc_aioclient_mock.call_count == 6

    state = hass.states.get("sensor.esios_pvpc")
    state_inyection = hass.states.get("sensor.esios_injection_price")
    state_mag = hass.states.get("sensor.esios_mag_tax")
    state_omie = hass.states.get("sensor.esios_omie_price")
    check_valid_state(state, tariff=TARIFFS[1])
    assert state_inyection.state == "unavailable"
    assert not state_mag
    assert not state_omie