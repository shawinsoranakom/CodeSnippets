async def test_ordered_list_item_to_percentage() -> None:
    """Test percentage of an item in an ordered list."""

    assert ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_LOW) == 33
    assert ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_MEDIUM) == 66
    assert ordered_list_item_to_percentage(LEGACY_ORDERED_LIST, SPEED_HIGH) == 100

    assert ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_1) == 25
    assert ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_2) == 50
    assert ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_3) == 75
    assert ordered_list_item_to_percentage(SMALL_ORDERED_LIST, SPEED_4) == 100

    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_1) == 14
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_2) == 28
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_3) == 42
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_4) == 57
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_5) == 71
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_6) == 85
    assert ordered_list_item_to_percentage(LARGE_ORDERED_LIST, SPEED_7) == 100

    with pytest.raises(ValueError):
        assert ordered_list_item_to_percentage([], SPEED_1)