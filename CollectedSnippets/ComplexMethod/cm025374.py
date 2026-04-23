def build_item_response(
    media_library: MusicLibrary, payload: dict[str, str], get_thumbnail_url=None
) -> BrowseMedia | None:
    """Create response payload for the provided media query."""
    if payload["search_type"] == MediaType.ALBUM and payload["idstring"].startswith(
        ("A:GENRE", "A:COMPOSER")
    ):
        payload["idstring"] = "A:ALBUMARTIST/" + "/".join(
            payload["idstring"].split("/")[2:]
        )
        payload["idstring"] = urllib.parse.unquote(payload["idstring"])

    try:
        search_type = MEDIA_TYPES_TO_SONOS[payload["search_type"]]
    except KeyError:
        _LOGGER.debug(
            "Unknown media type received when building item response: %s",
            payload["search_type"],
        )
        return None

    media = media_library.browse_by_idstring(
        search_type,
        payload["idstring"],
        full_album_art_uri=True,
        max_items=0,
    )

    if media is None:
        return None

    thumbnail = None
    title = None

    # Fetch album info for titles and thumbnails
    # Can't be extracted from track info
    if (
        payload["search_type"] == MediaType.ALBUM
        and media[0].item_class == "object.item.audioItem.musicTrack"
    ):
        idstring = payload["idstring"]
        if idstring.startswith("A:ALBUMARTIST/"):
            search_type = SONOS_ALBUM_ARTIST
        elif idstring.startswith("A:ALBUM/"):
            search_type = SONOS_ALBUM
        item = get_media(media_library, idstring, search_type)

        title = getattr(item, "title", None)
        thumbnail = get_thumbnail_url(search_type, payload["idstring"])

    if not title:
        title = _get_title(id_string=payload["idstring"])

    try:
        media_class = SONOS_TO_MEDIA_CLASSES[
            MEDIA_TYPES_TO_SONOS[payload["search_type"]]
        ]
    except KeyError:
        _LOGGER.debug("Unknown media type received %s", payload["search_type"])
        return None

    children = []
    for item in media:
        with suppress(UnknownMediaType):
            children.append(item_payload(item, get_thumbnail_url))

    return BrowseMedia(
        title=title,
        thumbnail=thumbnail,
        media_class=media_class,
        media_content_id=payload["idstring"],
        media_content_type=payload["search_type"],
        children=children,
        can_play=can_play(payload["search_type"]),
        can_expand=can_expand(payload["search_type"]),
    )