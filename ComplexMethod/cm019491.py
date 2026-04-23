async def test_media_browse_service(hass: HomeAssistant) -> None:
    """Test browsing media using service call."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value=BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id="mock-id",
            media_content_type="mock-type",
            title="Mock Title",
            can_play=False,
            can_expand=True,
            children=[
                BrowseMedia(
                    media_class=MediaClass.ALBUM,
                    media_content_id="album1 content id",
                    media_content_type="album",
                    title="Album 1",
                    can_play=True,
                    can_expand=True,
                ),
                BrowseMedia(
                    media_class=MediaClass.ALBUM,
                    media_content_id="album2 content id",
                    media_content_type="album",
                    title="Album 2",
                    can_play=True,
                    can_expand=True,
                ),
            ],
        ),
    ) as mock_browse_media:
        result = await hass.services.async_call(
            "media_player",
            SERVICE_BROWSE_MEDIA,
            {
                ATTR_ENTITY_ID: "media_player.browse",
                ATTR_MEDIA_CONTENT_TYPE: "album",
                ATTR_MEDIA_CONTENT_ID: "title=Album*",
            },
            blocking=True,
            return_response=True,
        )

        mock_browse_media.assert_called_with(
            media_content_type="album", media_content_id="title=Album*"
        )
        browse_res: BrowseMedia = result["media_player.browse"]
        assert browse_res.title == "Mock Title"
        assert browse_res.media_class == "directory"
        assert browse_res.media_content_type == "mock-type"
        assert browse_res.media_content_id == "mock-id"
        assert browse_res.can_play is False
        assert browse_res.can_expand is True
        assert len(browse_res.children) == 2
        assert browse_res.children[0].title == "Album 1"
        assert browse_res.children[0].media_class == "album"
        assert browse_res.children[0].media_content_id == "album1 content id"
        assert browse_res.children[0].media_content_type == "album"
        assert browse_res.children[1].title == "Album 2"
        assert browse_res.children[1].media_class == "album"
        assert browse_res.children[1].media_content_id == "album2 content id"
        assert browse_res.children[1].media_content_type == "album"