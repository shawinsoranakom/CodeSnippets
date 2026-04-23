async def item_payload(item, get_thumbnail_url=None):
    """Create response payload for a single media item.

    Used by async_browse_media.
    """
    title = item["label"]

    media_class = None

    if "songid" in item:
        media_content_type = MediaType.TRACK
        media_content_id = f"{item['songid']}"
        can_play = True
        can_expand = False
    elif "albumid" in item:
        media_content_type = MediaType.ALBUM
        media_content_id = f"{item['albumid']}"
        can_play = True
        can_expand = True
    elif "artistid" in item:
        media_content_type = MediaType.ARTIST
        media_content_id = f"{item['artistid']}"
        can_play = True
        can_expand = True
    elif "movieid" in item:
        media_content_type = MediaType.MOVIE
        media_content_id = f"{item['movieid']}"
        can_play = True
        can_expand = False
    elif "episodeid" in item:
        media_content_type = MediaType.EPISODE
        media_content_id = f"{item['episodeid']}"
        can_play = True
        can_expand = False
    elif "seasonid" in item:
        media_content_type = MediaType.SEASON
        media_content_id = f"{item['tvshowid']}/{item['season']}"
        can_play = False
        can_expand = True
    elif "tvshowid" in item:
        media_content_type = MediaType.TVSHOW
        media_content_id = f"{item['tvshowid']}"
        can_play = False
        can_expand = True
    elif "channelid" in item:
        media_content_type = MediaType.CHANNEL
        media_content_id = f"{item['channelid']}"
        if broadcasting := item.get("broadcastnow"):
            show = broadcasting.get("title")
            title = f"{title} - {show}"
        can_play = True
        can_expand = False
    else:
        # this case is for the top folder of each type
        # possible content types: album, artist, movie, library_music, tvshow, channel
        media_class = MediaClass.DIRECTORY
        media_content_type = item["type"]
        media_content_id = ""
        can_play = False
        can_expand = True

    if media_class is None:
        try:
            media_class = CHILD_TYPE_MEDIA_CLASS[media_content_type]
        except KeyError as err:
            _LOGGER.debug("Unknown media type received: %s", media_content_type)
            raise UnknownMediaType from err

    if "art" in item:
        thumbnail = item["art"].get("poster", item.get("thumbnail"))
    else:
        thumbnail = item.get("thumbnail")
    if thumbnail is not None and get_thumbnail_url is not None:
        thumbnail = await get_thumbnail_url(
            media_content_type, media_content_id, thumbnail_url=thumbnail
        )

    return BrowseMedia(
        title=title,
        media_class=media_class,
        media_content_type=media_content_type,
        media_content_id=media_content_id,
        can_play=can_play,
        can_expand=can_expand,
        thumbnail=thumbnail,
    )