async def test_media_player_services(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Devialet services."""
    entry = await setup_integration(
        hass, aioclient_mock, state=MediaPlayerState.PLAYING
    )

    assert entry.state is ConfigEntryState.LOADED

    target = {ATTR_ENTITY_ID: hass.states.get(f"{MP_DOMAIN}.{NAME}").entity_id}

    for i, (service, urls) in enumerate(SERVICE_TO_URL.items()):
        for url in urls:
            aioclient_mock.post(f"http://{HOST}{url}")

        for data_set in list(SERVICE_TO_DATA.values())[i]:
            service_data = target.copy()
            service_data.update(data_set)

            await hass.services.async_call(
                MP_DOMAIN,
                service,
                service_data=service_data,
                blocking=True,
            )
            await hass.async_block_till_done()

        for url in urls:
            call_available = False
            for item in aioclient_mock.mock_calls:
                if item[0] == "POST" and item[1] == URL(f"http://{HOST}{url}"):
                    call_available = True
                    break

            assert call_available

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED