async def test_update_device_labels(
    hass: HomeAssistant,
    client: MockHAClientWebSocket,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update entry labels."""
    entry = MockConfigEntry(title=None)
    entry.add_to_hass(hass)
    created_at = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_at)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={("ethernet", "12:34:56:78:90:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )

    assert not device.labels
    modified_at = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "type": "config/device_registry/update",
            "device_id": device.id,
            "labels": ["label1", "label2"],
        }
    )

    msg = await client.receive_json()
    await hass.async_block_till_done()
    assert len(device_registry.devices) == 1

    device = device_registry.async_get_device(
        identifiers={("bridgeid", "0123")},
        connections={("ethernet", "12:34:56:78:90:AB:CD:EF")},
    )

    assert msg["result"]["labels"] == unordered(["label1", "label2"])
    assert device.labels == {"label1", "label2"}
    for key, value in (
        ("created_at", created_at),
        ("modified_at", modified_at),
    ):
        assert msg["result"][key] == value.timestamp()
        assert getattr(device, key) == value