async def test_inputselector(hass: HomeAssistant) -> None:
    """Test input selector trait."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None
    assert trait.InputSelectorTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.SELECT_SOURCE,
        None,
        None,
    )

    trt = trait.InputSelectorTrait(
        hass,
        State(
            "media_player.living_room",
            media_player.STATE_PLAYING,
            attributes={
                media_player.ATTR_INPUT_SOURCE_LIST: [
                    "media",
                    "game",
                    "chromecast",
                    "plex",
                ],
                media_player.ATTR_INPUT_SOURCE: "game",
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableInputs": [
            {"key": "media", "names": [{"name_synonym": ["media"], "lang": "en"}]},
            {"key": "game", "names": [{"name_synonym": ["game"], "lang": "en"}]},
            {
                "key": "chromecast",
                "names": [{"name_synonym": ["chromecast"], "lang": "en"}],
            },
            {"key": "plex", "names": [{"name_synonym": ["plex"], "lang": "en"}]},
        ],
        "orderedInputs": True,
    }

    assert trt.query_attributes() == {
        "currentInput": "game",
    }

    assert trt.can_execute(
        trait.COMMAND_SET_INPUT,
        params={"newInput": "media"},
    )

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_SELECT_SOURCE
    )
    await trt.execute(
        trait.COMMAND_SET_INPUT,
        BASIC_DATA,
        {"newInput": "media"},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": "media_player.living_room", "source": "media"}