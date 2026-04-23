async def test_play_media(hass: HomeAssistant) -> None:
    """Test playing media."""
    calls = async_mock_service(hass, "cast", "show_lovelace_view")

    await lovelace_cast.async_play_media(
        hass, "media_player.my_cast", None, "lovelace", lovelace_cast.DEFAULT_DASHBOARD
    )

    assert len(calls) == 1
    assert calls[0].data["entity_id"] == "media_player.my_cast"
    assert "dashboard_path" not in calls[0].data
    assert calls[0].data["view_path"] == "0"

    await lovelace_cast.async_play_media(
        hass, "media_player.my_cast", None, "lovelace", "yaml-with-views/second-view"
    )

    assert len(calls) == 2
    assert calls[1].data["entity_id"] == "media_player.my_cast"
    assert calls[1].data["dashboard_path"] == "yaml-with-views"
    assert calls[1].data["view_path"] == "second-view"