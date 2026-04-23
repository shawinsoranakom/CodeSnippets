async def test_level_controllable_output_cover(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry_factory: ConfigEntryFactoryType,
    mock_put_request: Callable[[str, str], AiohttpClientMocker],
    snapshot: SnapshotAssertion,
) -> None:
    """Test that tilting a cover works."""
    with patch("homeassistant.components.deconz.PLATFORMS", [Platform.COVER]):
        config_entry = await config_entry_factory()
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)

    # Verify service calls for tilting cover

    aioclient_mock = mock_put_request("/lights/0/state")

    # Service open cover

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": False}

    # Service close cover

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"on": True}

    # Service set cover position

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: "cover.vent", ATTR_POSITION: 40},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"bri": 152}

    # Service set tilt cover

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: "cover.vent", ATTR_TILT_POSITION: 40},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"sat": 152}

    # Service open tilt cover

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[5][2] == {"sat": 0}

    # Service close tilt cover

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[6][2] == {"sat": 254}

    # Service stop cover movement

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[7][2] == {"bri_inc": 0}