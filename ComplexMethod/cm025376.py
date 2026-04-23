def get_media(
    media_library: MusicLibrary, item_id: str, search_type: str
) -> MusicServiceItem | None:
    """Fetch a single media/album."""
    _LOGGER.debug("get_media item_id [%s], search_type [%s]", item_id, search_type)
    search_type = MEDIA_TYPES_TO_SONOS.get(search_type, search_type)

    if search_type == "playlists":
        # Format is S:TITLE or S:ITEM_ID
        splits = item_id.split(":")
        title = splits[1] if len(splits) > 1 else None
        return next(
            (
                p
                for p in media_library.get_playlists()
                if (item_id == p.item_id or title == p.title)
            ),
            None,
        )

    if not item_id.startswith("A:ALBUM") and search_type == SONOS_ALBUM:
        item_id = "A:ALBUMARTIST/" + "/".join(item_id.split("/")[2:])

    if item_id.startswith("A:ALBUM/") or search_type == "tracks":
        # Some Sonos libraries return album ids in the shape:
        # A:ALBUM/<album>/<artist>, where the artist part disambiguates results.
        # Use the album segment for searching.
        if item_id.startswith("A:ALBUM/"):
            splits = item_id.split("/")
            search_term = urllib.parse.unquote(splits[1]) if len(splits) > 1 else ""
            album_title: str | None = search_term
        else:
            search_term = urllib.parse.unquote(item_id.split("/")[-1])
            album_title = None

        matches = media_library.get_music_library_information(
            search_type, search_term=search_term, full_album_art_uri=True
        )
        if item_id.startswith("A:ALBUM/") and len(matches) > 1:
            if result := next(
                (item for item in matches if item_id == item.item_id), None
            ):
                matches = [result]
            elif album_title:
                if result := next(
                    (item for item in matches if album_title == item.title), None
                ):
                    matches = [result]
    elif search_type == SONOS_SHARE:
        # In order to get the MusicServiceItem, we browse the parent folder
        # and find one that matches on item_id.
        parts = item_id.rstrip("/").split("/")
        parent_folder = "/".join(parts[:-1])
        matches = media_library.browse_by_idstring(
            search_type, parent_folder, full_album_art_uri=True
        )
        result = next(
            (item for item in matches if (item_id == item.item_id)),
            None,
        )
        matches = [result]
    else:
        # When requesting media by album_artist, composer, genre use the browse interface
        # to navigate the hierarchy. This occurs when invoked from media browser or service
        # calls
        # Example: A:ALBUMARTIST/Neil Young/Greatest Hits - get specific album
        # Example: A:ALBUMARTIST/Neil Young - get all albums
        # Others: composer, genre
        # A:<topic>/<name>/<optional title>
        splits = item_id.split("/")
        title = urllib.parse.unquote(splits[2]) if len(splits) > 2 else None
        browse_id_string = splits[0] + "/" + splits[1]
        matches = media_library.browse_by_idstring(
            search_type, browse_id_string, full_album_art_uri=True
        )
        if title:
            result = next(
                (item for item in matches if (title == item.title)),
                None,
            )
            matches = [result]

    _LOGGER.debug(
        "get_media search_type [%s] item_id [%s] matches [%d]",
        search_type,
        item_id,
        len(matches),
    )
    if len(matches) > 0:
        return matches[0]
    return None