async def test_blindtilt_controlling(
    hass: HomeAssistant, mock_entry_factory: Callable[[str], MockConfigEntry]
) -> None:
    """Test blindtilt controlling."""
    inject_bluetooth_service_info(hass, WOBLINDTILT_SERVICE_INFO)

    entry = mock_entry_factory(sensor_type="blind_tilt")
    entry.add_to_hass(hass)
    info = {
        "motionDirection": {
            "opening": False,
            "closing": False,
            "up": False,
            "down": False,
        },
    }
    with (
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.get_basic_info",
            new=AsyncMock(return_value=info),
        ),
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.open",
            new=AsyncMock(return_value=True),
        ) as mock_open,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.close",
            new=AsyncMock(return_value=True),
        ) as mock_close,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.stop",
            new=AsyncMock(return_value=True),
        ) as mock_stop,
        patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.set_position",
            new=AsyncMock(return_value=True),
        ) as mock_set_position,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "cover.test_name"
        address = "AA:BB:CC:DD:EE:FF"
        service_data = b"x\x00*"

        # Test open
        manufacturer_data = b"\xfbgA`\x98\xe8\x1d%F\x12\x85"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_open.assert_awaited_once()

            state = hass.states.get(entity_id)
            assert state.state == CoverState.OPEN
            assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 70

        # Test close
        manufacturer_data = b"\xfbgA`\x98\xe8\x1d%\x0f\x12\x85"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_close.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.CLOSED
            assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 15

        # Test stop
        manufacturer_data = b"\xfbgA`\x98\xe8\x1d%\n\x12\x85"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER_TILT,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_stop.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.CLOSED
            assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 10

        # Test set position
        manufacturer_data = b"\xfbgA`\x98\xe8\x1d%2\x12\x85"
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_TILT_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_TILT_POSITION: 50},
            blocking=True,
        )
        with patch(
            "homeassistant.components.switchbot.cover.switchbot.SwitchbotBlindTilt.get_basic_info",
            return_value=info,
        ):
            inject_bluetooth_service_info(
                hass, make_advertisement(address, manufacturer_data, service_data)
            )
            await hass.async_block_till_done()

            mock_set_position.assert_awaited_once()
            state = hass.states.get(entity_id)
            assert state.state == CoverState.OPEN
            assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 50