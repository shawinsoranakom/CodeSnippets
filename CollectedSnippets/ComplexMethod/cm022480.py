async def test_channel(hass: HomeAssistant) -> None:
    """Test Channel trait support."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None
    assert trait.ChannelTrait.supported(
        media_player.DOMAIN,
        MediaPlayerEntityFeature.PLAY_MEDIA,
        media_player.MediaPlayerDeviceClass.TV,
        None,
    )
    assert (
        trait.ChannelTrait.supported(
            media_player.DOMAIN,
            MediaPlayerEntityFeature.PLAY_MEDIA,
            None,
            None,
        )
        is False
    )
    assert trait.ChannelTrait.supported(media_player.DOMAIN, 0, None, None) is False

    trt = trait.ChannelTrait(hass, State("media_player.demo", STATE_ON), BASIC_CONFIG)

    assert trt.sync_attributes() == {
        "availableChannels": [],
        "commandOnlyChannels": True,
    }
    assert trt.query_attributes() == {}

    media_player_calls = async_mock_service(
        hass, media_player.DOMAIN, SERVICE_PLAY_MEDIA
    )
    await trt.execute(
        trait.COMMAND_SELECT_CHANNEL, BASIC_DATA, {"channelNumber": "1"}, {}
    )
    assert len(media_player_calls) == 1
    assert media_player_calls[0].data == {
        ATTR_ENTITY_ID: "media_player.demo",
        media_player.ATTR_MEDIA_CONTENT_ID: "1",
        media_player.ATTR_MEDIA_CONTENT_TYPE: MediaType.CHANNEL,
    }

    with pytest.raises(SmartHomeError, match="Channel is not available"):
        await trt.execute(
            trait.COMMAND_SELECT_CHANNEL, BASIC_DATA, {"channelCode": "Channel 3"}, {}
        )
    assert len(media_player_calls) == 1

    with pytest.raises(SmartHomeError, match="Unsupported command"):
        await trt.execute("Unknown command", BASIC_DATA, {"channelNumber": "1"}, {})
    assert len(media_player_calls) == 1