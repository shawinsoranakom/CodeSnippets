async def test_remove_entry(
    hass: HomeAssistant,
    setup_base_platform: PlatformSetup,
    aioclient_mock: AiohttpClientMocker,
    subscriber: AsyncMock,
) -> None:
    """Test successful unload of a ConfigEntry."""
    await setup_base_platform()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.state is ConfigEntryState.LOADED
    # Assert entry was imported if from configuration.yaml
    assert entry.data.get("subscriber_id") == SUBSCRIBER_ID
    assert entry.data.get("project_id") == PROJECT_ID

    aioclient_mock.clear_requests()
    aioclient_mock.delete(
        f"https://pubsub.googleapis.com/v1/{SUBSCRIBER_ID}",
        json={},
    )

    assert not subscriber.stop.called

    assert await hass.config_entries.async_remove(entry.entry_id)

    assert aioclient_mock.call_count == 1
    assert subscriber.stop.called

    entries = hass.config_entries.async_entries(DOMAIN)
    assert not entries