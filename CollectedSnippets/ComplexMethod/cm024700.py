async def test_poll_firmware_version_only_all_watchable_accessory_mode(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we only poll firmware if available and all chars are watchable accessory mode."""

    def _create_accessory(accessory: Accessory) -> Service:
        service = accessory.add_service(ServicesTypes.LIGHTBULB, name="TestDevice")

        on_char = service.add_char(CharacteristicsTypes.ON)
        on_char.value = 0

        brightness = service.add_char(CharacteristicsTypes.BRIGHTNESS)
        brightness.value = 0

        return service

    helper = await setup_test_component(hass, get_next_aid(), _create_accessory)

    with mock.patch.object(
        helper.pairing,
        "get_characteristics",
        wraps=helper.pairing.get_characteristics,
    ) as mock_get_characteristics:
        # Initial state is that the light is off
        state = await helper.poll_and_get_state()
        assert state.state == STATE_OFF
        assert mock_get_characteristics.call_count == 2
        # Verify everything is polled (convert to set for comparison since batching changes the type)
        assert set(mock_get_characteristics.call_args_list[0][0][0]) == {
            (1, 10),
            (1, 11),
        }
        assert set(mock_get_characteristics.call_args_list[1][0][0]) == {
            (1, 10),
            (1, 11),
        }

        # Test device goes offline
        helper.pairing.available = False
        with mock.patch.object(
            FakeController,
            "async_reachable",
            return_value=False,
        ):
            state = await helper.poll_and_get_state()
            assert state.state == STATE_UNAVAILABLE
            # Tries twice before declaring unavailable
            assert mock_get_characteristics.call_count == 4

        # Test device comes back online
        helper.pairing.available = True
        state = await helper.poll_and_get_state()
        assert state.state == STATE_OFF
        assert mock_get_characteristics.call_count == 6

        # Next poll should not happen because its a single
        # accessory, available, and all chars are watchable
        state = await helper.poll_and_get_state()
        assert state.state == STATE_OFF
        assert mock_get_characteristics.call_count == 8