async def test_lock_without_pullspring(
    hass: HomeAssistant,
    mock_tedee: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the tedee lock without pullspring."""
    # Fetch translations
    await async_setup_component(hass, "homeassistant", {})

    state = hass.states.get("lock.lock_2c3d")
    assert state
    assert state == snapshot

    entry = entity_registry.async_get(state.entity_id)
    assert entry
    assert entry == snapshot

    assert entry.device_id
    device = device_registry.async_get(entry.device_id)
    assert device
    assert device == snapshot

    with pytest.raises(
        ServiceNotSupported,
        match=f"Entity lock.lock_2c3d does not support action {LOCK_DOMAIN}.{SERVICE_OPEN}",
    ):
        await hass.services.async_call(
            LOCK_DOMAIN,
            SERVICE_OPEN,
            {
                ATTR_ENTITY_ID: "lock.lock_2c3d",
            },
            blocking=True,
        )

    assert len(mock_tedee.open.mock_calls) == 0