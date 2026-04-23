async def test_detect_location_info_whoami(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    session: aiohttp.ClientSession,
) -> None:
    """Test detect location info using services.home-assistant.io/whoami."""
    aioclient_mock.get(
        location_util.WHOAMI_URL, text=await async_load_fixture(hass, "whoami.json")
    )

    with patch("homeassistant.util.location.HA_VERSION", "1.0"):
        info = await location_util.async_detect_location_info(session, _test_real=True)

    assert str(aioclient_mock.mock_calls[-1][1]) == location_util.WHOAMI_URL

    assert info is not None
    assert info.ip == "1.2.3.4"
    assert info.country_code == "XX"
    assert info.currency == "XXX"
    assert info.region_code == "00"
    assert info.city == "Gotham"
    assert info.zip_code == "12345"
    assert info.time_zone == "Earth/Gotham"
    assert info.latitude == 12.34567
    assert info.longitude == 12.34567
    assert info.use_metric