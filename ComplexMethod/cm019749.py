async def test_cover_services(
    hass: HomeAssistant,
    normal_config_entry: MockConfigEntry,
) -> None:
    """Tests that the cover entities are correct."""

    await setup_platform(hass, normal_config_entry, [Platform.COVER])

    # Vent Windows
    entity_id = "cover.test_windows"
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.window_control",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

        call.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: ["cover.test_windows"]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.CLOSED

    # Charge Port Door
    entity_id = "cover.test_charge_port_door"
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.charge_port_door_open",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.charge_port_door_close",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.CLOSED

    # Frunk
    entity_id = "cover.test_frunk"
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.actuate_trunk",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

    # Trunk
    entity_id = "cover.test_trunk"
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.actuate_trunk",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

        call.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.CLOSED

    # Sunroof
    entity_id = "cover.test_sunroof"
    with patch(
        "tesla_fleet_api.tesla.VehicleFleet.sun_roof_control",
        return_value=COMMAND_OK,
    ) as call:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

        call.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.OPEN

        call.reset_mock()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
        call.assert_called_once()
        state = hass.states.get(entity_id)
        assert state
        assert state.state == CoverState.CLOSED