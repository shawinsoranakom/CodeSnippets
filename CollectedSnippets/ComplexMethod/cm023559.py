async def test_curtain3_controlling(
    hass: HomeAssistant, mock_entry_factory: Callable[[str], MockConfigEntry]
) -> None:
    """Test Curtain3 controlling."""
    inject_bluetooth_service_info(hass, WOCURTAIN3_SERVICE_INFO)

    entry = mock_entry_factory(sensor_type="curtain")
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotCurtain.open",
            new=AsyncMock(return_value=True),
        ) as mock_open,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotCurtain.close",
            new=AsyncMock(return_value=True),
        ) as mock_close,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotCurtain.stop",
            new=AsyncMock(return_value=True),
        ) as mock_stop,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotCurtain.set_position",
            new=AsyncMock(return_value=True),
        ) as mock_set_position,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "cover.test_name"
        address = "AA:BB:CC:DD:EE:FF"
        service_data = b"{\xc06\x00\x11D"

        # Test open
        manufacturer_data = b"\xcf;Zwu\x0c\x19\x0b\x05\x11D\x006"
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        inject_bluetooth_service_info(
            hass, make_advertisement(address, manufacturer_data, service_data)
        )
        await hass.async_block_till_done()

        mock_open.assert_awaited_once_with(255)  # Default speed
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPEN
        assert state.attributes[ATTR_CURRENT_POSITION] == 95

        # Test close
        manufacturer_data = b"\xcf;Zwu\x0c\x19\x0b\x58\x11D\x006"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        inject_bluetooth_service_info(
            hass, make_advertisement(address, manufacturer_data, service_data)
        )
        await hass.async_block_till_done()

        mock_close.assert_awaited_once_with(255)  # Default speed
        state = hass.states.get(entity_id)
        assert state.state == CoverState.CLOSED
        assert state.attributes[ATTR_CURRENT_POSITION] == 12

        # Test stop
        manufacturer_data = b"\xcf;Zwu\x0c\x19\x0b\x3c\x11D\x006"
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        inject_bluetooth_service_info(
            hass, make_advertisement(address, manufacturer_data, service_data)
        )
        await hass.async_block_till_done()

        mock_stop.assert_awaited_once()
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPEN
        assert state.attributes[ATTR_CURRENT_POSITION] == 40

        # Test set position
        manufacturer_data = b"\xcf;Zwu\x0c\x19\x0b(\x11D\x006"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
            blocking=True,
        )
        inject_bluetooth_service_info(
            hass, make_advertisement(address, manufacturer_data, service_data)
        )
        await hass.async_block_till_done()

        mock_set_position.assert_awaited_once()
        state = hass.states.get(entity_id)
        assert state.state == CoverState.OPEN
        assert state.attributes[ATTR_CURRENT_POSITION] == 60