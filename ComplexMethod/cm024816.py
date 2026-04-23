async def test_percentage_to_ordered_list_item() -> None:
    """Test item that most closely matches the percentage in an ordered list."""

    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 1) == SPEED_1
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 25) == SPEED_1
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 26) == SPEED_2
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 50) == SPEED_2
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 51) == SPEED_3
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 75) == SPEED_3
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 76) == SPEED_4
    assert percentage_to_ordered_list_item(SMALL_ORDERED_LIST, 100) == SPEED_4

    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 17) == SPEED_LOW
    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 33) == SPEED_LOW
    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 50) == SPEED_MEDIUM
    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 66) == SPEED_MEDIUM
    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 84) == SPEED_HIGH
    assert percentage_to_ordered_list_item(LEGACY_ORDERED_LIST, 100) == SPEED_HIGH

    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 1) == SPEED_1
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 14) == SPEED_1
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 25) == SPEED_2
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 26) == SPEED_2
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 28) == SPEED_2
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 29) == SPEED_3
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 41) == SPEED_3
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 42) == SPEED_3
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 43) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 56) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 50) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 51) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 75) == SPEED_6
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 76) == SPEED_6
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100) == SPEED_7

    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 1) == SPEED_1
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 25) == SPEED_2
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 26) == SPEED_2
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 50) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 51) == SPEED_4
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 75) == SPEED_6
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 76) == SPEED_6
    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100) == SPEED_7

    assert percentage_to_ordered_list_item(LARGE_ORDERED_LIST, 100.1) == SPEED_7

    with pytest.raises(ValueError):
        assert percentage_to_ordered_list_item([], 100)