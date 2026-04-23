async def test_services_play_media_local_source(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_roku: MagicMock,
) -> None:
    """Test the media player services related to playing media."""
    local_media = hass.config.path("media")
    await async_process_ha_core_config(
        hass, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "media_source", {})
    await hass.async_block_till_done()

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: MAIN_ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: "video/mp4",
            ATTR_MEDIA_CONTENT_ID: "media-source://media_source/local/Epic Sax Guy 10 Hours.mp4",
        },
        blocking=True,
    )

    assert mock_roku.launch.call_count == 1
    assert mock_roku.launch.call_args
    call_args = mock_roku.launch.call_args.args
    assert call_args[0] == DEFAULT_PLAY_MEDIA_APP_ID
    assert "u" in call_args[1]
    assert "/local/Epic%20Sax%20Guy%2010%20Hours.mp4?authSig=" in call_args[1]["u"]
    assert "t" in call_args[1]
    assert call_args[1]["t"] == "v"
    assert "videoFormat" in call_args[1]
    assert call_args[1]["videoFormat"] == "mp4"
    assert "videoName" in call_args[1]
    assert (
        call_args[1]["videoName"]
        == "media-source://media_source/local/Epic Sax Guy 10 Hours.mp4"
    )