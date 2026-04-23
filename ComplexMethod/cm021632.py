def test_games_reformat_to_dict(
    hass: HomeAssistant, patch_load_json_object: MagicMock
) -> None:
    """Test old data format is converted to new format."""
    patch_load_json_object.return_value = MOCK_GAMES_DATA_OLD_STR_FORMAT
    with (
        patch("homeassistant.components.ps4.save_json", side_effect=MagicMock()),
        patch("os.path.isfile", return_value=True),
    ):
        mock_games = ps4.load_games(hass, MOCK_ENTRY_ID)

    # New format is a nested dict.
    assert isinstance(mock_games, dict)
    assert mock_games["mock_id"][ATTR_MEDIA_TITLE] == "mock_title"
    assert mock_games["mock_id2"][ATTR_MEDIA_TITLE] == "mock_title2"
    for mock_game in mock_games:
        mock_data = mock_games[mock_game]
        assert isinstance(mock_data, dict)
        assert mock_data
        assert mock_data[ATTR_MEDIA_IMAGE_URL] is None
        assert mock_data[ATTR_LOCKED] is False
        assert mock_data[ATTR_MEDIA_CONTENT_TYPE] == MediaType.GAME