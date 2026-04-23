def test_format_game_data() -> None:
    """Test game data format."""
    game_data = format_game_data(
        GAMES_TO_TEST_FREE_OR_DISCOUNT[0]["raw_game_data"], "fr"
    )
    assert game_data
    assert game_data["title"]
    assert game_data["description"]
    assert game_data["released_at"]
    assert game_data["original_price"]
    assert game_data["publisher"]
    assert game_data["url"]
    assert game_data["img_portrait"]
    assert game_data["img_landscape"]
    assert game_data["discount_type"] == "free"
    assert game_data["discount_start_at"]
    assert game_data["discount_end_at"]