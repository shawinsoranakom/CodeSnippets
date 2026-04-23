async def test_diagnostic_entities(
    hass: HomeAssistant,
    knx: KNXTestKit,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test diagnostic entities."""
    await knx.setup_integration()

    for entity_id in (
        "sensor.knx_interface_individual_address",
        "sensor.knx_interface_connection_established",
        "sensor.knx_interface_connection_type",
        "sensor.knx_interface_incoming_telegrams",
        "sensor.knx_interface_incoming_telegram_errors",
        "sensor.knx_interface_outgoing_telegrams",
        "sensor.knx_interface_outgoing_telegram_errors",
        "sensor.knx_interface_telegrams",
        "sensor.knx_interface_undecodable_data_secure_telegrams",
    ):
        entity = entity_registry.async_get(entity_id)
        assert entity.entity_category is EntityCategory.DIAGNOSTIC

    for entity_id in (
        "sensor.knx_interface_incoming_telegrams",
        "sensor.knx_interface_outgoing_telegrams",
        "sensor.knx_interface_undecodable_data_secure_telegrams",
    ):
        entity = entity_registry.async_get(entity_id)
        assert entity.disabled is True

    knx.xknx.connection_manager.cemi_count_incoming = 20
    knx.xknx.connection_manager.cemi_count_incoming_error = 1
    knx.xknx.connection_manager.cemi_count_outgoing = 10
    knx.xknx.connection_manager.cemi_count_outgoing_error = 2

    events = async_capture_events(hass, "state_changed")
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(events) == 3  # 6 polled sensors - 3 disabled
    events.clear()

    for entity_id, test_state in (
        ("sensor.knx_interface_individual_address", "0.0.0"),
        ("sensor.knx_interface_connection_type", "Tunnel TCP"),
        # skipping connected_since timestamp
        ("sensor.knx_interface_incoming_telegram_errors", "1"),
        ("sensor.knx_interface_outgoing_telegram_errors", "2"),
        ("sensor.knx_interface_telegrams", "31"),
    ):
        assert hass.states.get(entity_id).state == test_state

    knx.xknx.connection_manager.connection_state_changed(
        state=XknxConnectionState.DISCONNECTED
    )
    await hass.async_block_till_done()
    assert len(events) == 4
    events.clear()

    knx.xknx.current_address = IndividualAddress("1.1.1")
    knx.xknx.connection_manager.connection_state_changed(
        state=XknxConnectionState.CONNECTED,
        connection_type=XknxConnectionType.TUNNEL_UDP,
    )
    await hass.async_block_till_done()
    assert len(events) == 6  # all diagnostic sensors - counters are reset on connect

    for entity_id, test_state in (
        ("sensor.knx_interface_individual_address", "1.1.1"),
        ("sensor.knx_interface_connection_type", "Tunnel UDP"),
        # skipping connected_since timestamp
        ("sensor.knx_interface_incoming_telegram_errors", "0"),
        ("sensor.knx_interface_outgoing_telegram_errors", "0"),
        ("sensor.knx_interface_telegrams", "0"),
    ):
        assert hass.states.get(entity_id).state == test_state