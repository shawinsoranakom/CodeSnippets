async def test_service_get_episodes_with_season_filter(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test get_episodes service with season filter."""
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_EPISODES,
        {
            ATTR_ENTRY_ID: init_integration.entry_id,
            "series_id": 105,
            "season_number": 1,
        },
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert ATTR_EPISODES in response
    episodes = response[ATTR_EPISODES]
    assert isinstance(episodes, dict)
    # Should only have season 1 episodes (2 of them)
    assert len(episodes) == 2
    assert "S01E01" in episodes
    assert "S01E02" in episodes
    assert "S02E01" not in episodes