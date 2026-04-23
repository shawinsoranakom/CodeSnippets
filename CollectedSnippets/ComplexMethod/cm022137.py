async def test_logbook_user_id_from_parent_context_state_changes_only(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test user attribution is inherited when only state changes are present.

    Same chain as the full test but without the EVENT_CALL_SERVICE event.
    This exercises the code path where context_lookup resolves the child
    context to the state change row itself, and augment walks up to the
    parent state change.
    """
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    await async_recorder_block_till_done(hass)

    # Set initial states so that subsequent changes are real state transitions
    hass.states.async_set(
        "climate.living_room",
        "off",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
    )
    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    # Parent context with user_id
    parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    # Climate state change with the parent context
    hass.states.async_set(
        "climate.living_room",
        "heat",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
        context=parent_context,
    )
    await hass.async_block_till_done()

    # Child context WITHOUT user_id, no service call event
    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id="01GTDGKBCH00GW0X476W5TVAAA",
    )

    # Switch state change with the child context
    hass.states.async_set(
        "switch.heater",
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Heater"},
        context=child_context,
    )
    await hass.async_block_till_done()

    # Climate updates again in response to switch state change
    hass.states.async_set(
        "climate.living_room",
        "heat",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
        context=child_context,
    )
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)
    end_time = start_date + timedelta(hours=24)

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    # Switch state change should be attributed to the climate entity
    # and inherit user_id from the parent context
    heater_entries = [
        entry for entry in json_dict if entry.get("entity_id") == "switch.heater"
    ]
    assert len(heater_entries) == 1

    heater_entry = heater_entries[0]
    assert heater_entry["context_entity_id"] == "climate.living_room"
    assert heater_entry["context_entity_id_name"] == "Living Room Thermostat"
    assert heater_entry["context_state"] == "heat"
    assert heater_entry["context_user_id"] == "b400facee45711eaa9308bfd3d19e474"