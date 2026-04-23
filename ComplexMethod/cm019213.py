async def test_restore_state(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test that we can restore state."""
    entry = MockConfigEntry(
        domain="owntracks", data={"webhook_id": "owntracks_test", "secret": "abcd"}
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_client()
    resp = await client.post(
        "/api/webhook/owntracks_test",
        json=LOCATION_MESSAGE,
        headers={"X-Limit-u": "Paulus", "X-Limit-d": "Pixel"},
    )
    assert resp.status == 200
    await hass.async_block_till_done()

    state_1 = hass.states.get("device_tracker.paulus_pixel")
    assert state_1 is not None

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    state_2 = hass.states.get("device_tracker.paulus_pixel")
    assert state_2 is not None

    assert state_1 is not state_2

    assert state_1.state == state_2.state
    assert state_1.name == state_2.name
    assert state_1.attributes["latitude"] == state_2.attributes["latitude"]
    assert state_1.attributes["longitude"] == state_2.attributes["longitude"]
    assert state_1.attributes["battery_level"] == state_2.attributes["battery_level"]
    assert state_1.attributes["source_type"] == state_2.attributes["source_type"]