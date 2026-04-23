async def test_binary_sensor(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_ring_client: Ring,
    mock_ring_event_listener_class: RingEventListener,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    device_id: int,
    device_name: str,
    alert_kind: str,
    device_class: str,
) -> None:
    """Test the Ring binary sensors."""
    # Create the entity so it is not ignored by the deprecation check
    mock_config_entry.add_to_hass(hass)

    entity_id = f"binary_sensor.{device_name}_{alert_kind}"
    unique_id = f"{device_id}-{alert_kind}"

    entity_registry.async_get_or_create(
        domain=BINARY_SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=unique_id,
        suggested_object_id=f"{device_name}_{alert_kind}",
        config_entry=mock_config_entry,
    )
    with patch("homeassistant.components.ring.PLATFORMS", [Platform.BINARY_SENSOR]):
        assert await async_setup_component(hass, DOMAIN, {})

    on_event_cb = mock_ring_event_listener_class.return_value.add_notification_callback.call_args.args[
        0
    ]

    # Default state is set to off

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes["device_class"] == device_class

    # A new alert sets to on
    event = RingEvent(
        1234546, device_id, "Foo", "Bar", time.time(), 180, kind=alert_kind, state=None
    )
    mock_ring_client.active_alerts.return_value = [event]
    on_event_cb(event)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # Test that another event resets the expiry callback
    freezer.tick(60)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    event = RingEvent(
        1234546, device_id, "Foo", "Bar", time.time(), 180, kind=alert_kind, state=None
    )
    mock_ring_client.active_alerts.return_value = [event]
    on_event_cb(event)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    freezer.tick(120)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # Test the second alert has expired
    freezer.tick(60)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF