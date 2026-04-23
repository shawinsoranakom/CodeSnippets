async def test_browsing_webrtc(hass: HomeAssistant) -> None:
    """Test browsing WebRTC camera media source."""
    # 3 cameras:
    # one only supports WebRTC (no stream source)
    # one raises when getting the source
    # One has a stream source, and should be the only browsable one
    with patch(
        "homeassistant.components.camera.Camera.stream_source",
        side_effect=["test", None, Exception],
    ):
        item = await media_source.async_browse_media(hass, "media-source://camera")
        assert item is not None
        assert item.title == "Camera"
        assert len(item.children) == 0
        assert item.not_shown == 3

        # Adding stream enables HLS camera
        hass.config.components.add("stream")

        item = await media_source.async_browse_media(hass, "media-source://camera")
        assert item.not_shown == 2
        assert len(item.children) == 1
        assert item.children[0].media_content_type == FORMAT_CONTENT_TYPE["hls"]