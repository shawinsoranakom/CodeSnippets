async def test_service_show_view(hass: HomeAssistant) -> None:
    """Test showing a view."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    await home_assistant_cast.async_setup_ha_cast(hass, entry)
    calls = async_mock_signal(hass, home_assistant_cast.SIGNAL_HASS_CAST_SHOW_VIEW)

    # No valid URL
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "cast",
            "show_lovelace_view",
            {"entity_id": "media_player.kitchen", "view_path": "mock_path"},
            blocking=True,
        )

    # Set valid URL
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )
    await hass.services.async_call(
        "cast",
        "show_lovelace_view",
        {"entity_id": "media_player.kitchen", "view_path": "mock_path"},
        blocking=True,
    )

    assert len(calls) == 1
    controller_data, entity_id, view_path, url_path = calls[0]
    assert controller_data["hass_url"] == "https://example.com"
    assert controller_data["client_id"] is None
    # Verify user did not accidentally submit their dev app id
    assert "supporting_app_id" not in controller_data
    assert entity_id == "media_player.kitchen"
    assert view_path == "mock_path"
    assert url_path is None