async def test_spaceapi_get(hass: HomeAssistant, mock_client: TestClient) -> None:
    """Test response after start-up Home Assistant."""
    resp = await mock_client.get(URL_API_SPACEAPI)
    assert resp.status == HTTPStatus.OK

    data = await resp.json()

    assert data["api"] == SPACEAPI_VERSION
    assert data["space"] == "Home"
    assert data["contact"]["email"] == "hello@home-assistant.io"
    assert data["location"]["address"] == "In your Home"
    assert data["location"]["lat"] == 32.87336
    assert data["location"]["lon"] == -117.22743
    assert data["state"]["open"] == "null"
    assert data["state"]["icon"]["open"] == "https://home-assistant.io/open.png"
    assert data["state"]["icon"]["closed"] == "https://home-assistant.io/close.png"
    assert data["spacefed"]["spacenet"] == bool(1)
    assert data["spacefed"]["spacesaml"] == bool(0)
    assert data["spacefed"]["spacephone"] == bool(1)
    assert data["cam"][0] == "https://home-assistant.io/cam1"
    assert data["cam"][1] == "https://home-assistant.io/cam2"
    assert data["stream"]["m4"] == "https://home-assistant.io/m4"
    assert data["stream"]["mjpeg"] == "https://home-assistant.io/mjpeg"
    assert data["stream"]["ustream"] == "https://home-assistant.io/ustream"
    assert data["feeds"]["blog"]["url"] == "https://home-assistant.io/blog"
    assert data["feeds"]["wiki"]["type"] == "mediawiki"
    assert data["feeds"]["wiki"]["url"] == "https://home-assistant.io/wiki"
    assert data["feeds"]["calendar"]["type"] == "ical"
    assert data["feeds"]["calendar"]["url"] == "https://home-assistant.io/calendar"
    assert (
        data["feeds"]["flicker"]["url"]
        == "https://www.flickr.com/photos/home-assistant"
    )
    assert data["cache"]["schedule"] == "m.02"
    assert data["projects"][0] == "https://home-assistant.io/projects/1"
    assert data["projects"][1] == "https://home-assistant.io/projects/2"
    assert data["projects"][2] == "https://home-assistant.io/projects/3"
    assert data["radio_show"][0]["name"] == "Radioshow"
    assert data["radio_show"][0]["url"] == "https://home-assistant.io/radio"
    assert data["radio_show"][0]["type"] == "ogg"
    assert data["radio_show"][0]["start"] == "2019-09-02T10:00Z"
    assert data["radio_show"][0]["end"] == "2019-09-02T12:00Z"