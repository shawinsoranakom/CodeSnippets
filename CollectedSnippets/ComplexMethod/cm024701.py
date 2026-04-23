async def test_characteristic_polling_batching(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that characteristic polling is batched to MAX_CHARACTERISTICS_PER_REQUEST."""

    # Create a large accessory with many characteristics (more than 49)
    def create_large_accessory_with_many_chars(accessory: Accessory) -> None:
        """Create an accessory with many characteristics to test batching."""
        # Add multiple services with many characteristics each
        for service_num in range(10):  # 10 services
            service = accessory.add_service(
                ServicesTypes.LIGHTBULB, name=f"Light {service_num}"
            )
            # Each lightbulb service gets several characteristics
            service.add_char(CharacteristicsTypes.ON)
            service.add_char(CharacteristicsTypes.BRIGHTNESS)
            service.add_char(CharacteristicsTypes.HUE)
            service.add_char(CharacteristicsTypes.SATURATION)
            service.add_char(CharacteristicsTypes.COLOR_TEMPERATURE)
            # Set initial values
            for char in service.characteristics:
                if char.type != CharacteristicsTypes.IDENTIFY:
                    char.value = 0

    helper = await setup_test_component(
        hass, get_next_aid(), create_large_accessory_with_many_chars
    )

    # Track the get_characteristics calls
    get_chars_calls = []
    original_get_chars = helper.pairing.get_characteristics

    async def mock_get_characteristics(chars):
        """Mock get_characteristics to track batch sizes."""
        get_chars_calls.append(list(chars))
        return await original_get_chars(chars)

    # Clear any calls from setup
    get_chars_calls.clear()

    # Patch get_characteristics to track calls
    with mock.patch.object(
        helper.pairing, "get_characteristics", side_effect=mock_get_characteristics
    ):
        # Trigger an update through time_changed which simulates regular polling
        # time_changed expects seconds, not a datetime
        await time_changed(hass, 300)  # 5 minutes in seconds
        await hass.async_block_till_done()

    # We created 10 lightbulb services with 5 characteristics each = 50 total
    # Plus any base accessory characteristics that are pollable
    # This should result in exactly 2 batches
    assert len(get_chars_calls) == 2, (
        f"Should have made exactly 2 batched calls, got {len(get_chars_calls)}"
    )

    # Check that no batch exceeded MAX_CHARACTERISTICS_PER_REQUEST
    for i, batch in enumerate(get_chars_calls):
        assert len(batch) <= MAX_CHARACTERISTICS_PER_REQUEST, (
            f"Batch {i} size {len(batch)} exceeded maximum {MAX_CHARACTERISTICS_PER_REQUEST}"
        )

    # Verify the total number of characteristics polled
    total_chars = sum(len(batch) for batch in get_chars_calls)
    # Each lightbulb has: ON, BRIGHTNESS, HUE, SATURATION, COLOR_TEMPERATURE = 5
    # 10 lightbulbs = 50 characteristics
    assert total_chars == 50, (
        f"Should have polled exactly 50 characteristics, got {total_chars}"
    )

    # The first batch should be full (49 characteristics)
    assert len(get_chars_calls[0]) == 49, (
        f"First batch should have exactly 49 characteristics, got {len(get_chars_calls[0])}"
    )

    # The second batch should have exactly 1 characteristic
    assert len(get_chars_calls[1]) == 1, (
        f"Second batch should have exactly 1 characteristic, got {len(get_chars_calls[1])}"
    )