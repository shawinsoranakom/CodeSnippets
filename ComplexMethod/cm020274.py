async def test_remove_entry_delete_subscriber_failure(
    hass: HomeAssistant,
    setup_base_platform: PlatformSetup,
    aioclient_mock: AiohttpClientMocker,
    subscriber: AsyncMock,
) -> None:
    """Test a failure when deleting the subscription."""
    await setup_base_platform()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.state is ConfigEntryState.LOADED

    aioclient_mock.clear_requests()
    aioclient_mock.delete(
        f"https://pubsub.googleapis.com/v1/{SUBSCRIBER_ID}",
        status=HTTPStatus.NOT_FOUND,
    )

    assert not subscriber.stop.called

    assert await hass.config_entries.async_remove(entry.entry_id)

    assert aioclient_mock.call_count == 1
    assert subscriber.stop.called

    entries = hass.config_entries.async_entries(DOMAIN)
    assert not entries