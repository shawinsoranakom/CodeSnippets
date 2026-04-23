async def test_roller_shade_controlling(
    hass: HomeAssistant, mock_entry_factory: Callable[[str], MockConfigEntry]
) -> None:
    """Test Roller Shade controlling."""
    inject_bluetooth_service_info(hass, ROLLER_SHADE_SERVICE_INFO)

    entry = mock_entry_factory(sensor_type="roller_shade")
    entry.add_to_hass(hass)
    info = {"battery": 39}
    with (
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.get_basic_info",
            new=AsyncMock(return_value=info),
        ),
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.open",
            new=AsyncMock(return_value=True),
        ) as mock_open,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.close",
            new=AsyncMock(return_value=True),
        ) as mock_close,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.stop",
            new=AsyncMock(return_value=True),
        ) as mock_stop,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.set_position",
            new=AsyncMock(return_value=True),
        ) as mock_set_position,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "cover.test_name"
        address = "AA:BB:CC:DD:EE:FF"
        service_data = b",\x00'\x9f\x11\x04"

        # Test open
        manufacturer_data = b"\xb0\xe9\xfeT\x90\x1b,\x08\xa0\x11\x04'\x00"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.get_basic_info",
            new=AsyncMock(return_value=info),
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_open.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.OPEN
            assert state.attributes[ATTR_CURRENT_POSITION] == 68

        # Test close
        manufacturer_data = b"\xb0\xe9\xfeT\x90\x1b,\x08\x5a\x11\x04'\x00"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_close.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.CLOSED
            assert state.attributes[ATTR_CURRENT_POSITION] == 10

        # Test stop
        manufacturer_data = b"\xb0\xe9\xfeT\x90\x1b,\x08\x5f\x11\x04'\x00"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_stop.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.CLOSED
            assert state.attributes[ATTR_CURRENT_POSITION] == 5

        # Test set position
        manufacturer_data = b"\xb0\xe9\xfeT\x90\x1b,\x08\x32\x11\x04'\x00"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 50},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotRollerShade.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_set_position.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.OPEN
            assert state.attributes[ATTR_CURRENT_POSITION] == 50