def test_get_items():
    res = get_items(
        "item_a",
        "item_b",
        "item_c",
        "item_d",
        "item_e",
    )
    assert res == ("item_a", "item_b", "item_c", "item_d", "item_e")