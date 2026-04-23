async def test_sound_modes(hass: HomeAssistant) -> None:
    """Test Mode trait."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None
    assert trait.ModesTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.SELECT_SOUND_MODE,
        None,
        None,
    )

    trt = trait.ModesTrait(
        hass,
        State(
            "media_player.living_room",
            media_player.STATE_PLAYING,
            attributes={
                media_player.ATTR_SOUND_MODE_LIST: ["stereo", "prologic"],
                media_player.ATTR_SOUND_MODE: "stereo",
            },
        ),
        BASIC_CONFIG,
    )

    attribs = trt.sync_attributes()
    assert attribs == {
        "availableModes": [
            {
                "name": "sound mode",
                "name_values": [
                    {"name_synonym": ["sound mode", "effects"], "lang": "en"}
                ],
                "settings": [
                    {
                        "setting_name": "stereo",
                        "setting_values": [
                            {"setting_synonym": ["stereo"], "lang": "en"}
                        ],
                    },
                    {
                        "setting_name": "prologic",
                        "setting_values": [
                            {"setting_synonym": ["prologic"], "lang": "en"}
                        ],
                    },
                ],
                "ordered": False,
            }
        ]
    }

    assert trt.query_attributes() == {
        "currentModeSettings": {"sound mode": "stereo"},
        "on": True,
    }

    assert trt.can_execute(
        trait.COMMAND_SET_MODES,
        params={"updateModeSettings": {"sound mode": "stereo"}},
    )

    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_SELECT_SOUND_MODE
    )
    await trt.execute(
        trait.COMMAND_SET_MODES,
        BASIC_DATA,
        {"updateModeSettings": {"sound mode": "stereo"}},
        {},
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "media_player.living_room",
        "sound_mode": "stereo",
    }