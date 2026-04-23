async def get_owntone_content(
    master: media_player.ForkedDaapdMaster,
    media_content_id: str,
) -> BrowseMedia:
    """Create response for the given media_content_id."""

    media_content = MediaContent(media_content_id)
    result: list[dict[str, int | str]] | dict[str, Any] | None = None
    if media_content.type == MediaType.APP:
        return base_owntone_library()
    # Query API for next level
    if media_content.type == MEDIA_TYPE_DIRECTORY:
        # returns tracks, directories, and playlists
        directory_path = media_content.id_or_path
        if directory_path:
            result = await master.api.get_directory(directory=directory_path)
        else:
            result = await master.api.get_directory()
        if result is None:
            raise BrowseError(
                f"Media not found for {media_content.type} / {media_content_id}"
            )
        # Fill in children with subdirectories
        children = []
        assert isinstance(result, dict)
        for directory in result["directories"]:
            path = directory["path"]
            children.append(
                BrowseMedia(
                    title=path,
                    media_class=MediaClass.DIRECTORY,
                    media_content_id=create_media_content_id(
                        title=path, media_type=MEDIA_TYPE_DIRECTORY, id_or_path=path
                    ),
                    media_content_type=MEDIA_TYPE_DIRECTORY,
                    can_play=False,
                    can_expand=True,
                )
            )
        result = result["tracks"]["items"] + result["playlists"]["items"]
        return create_browse_media_response(
            master,
            media_content,
            cast(list[dict[str, int | str]], result),
            children,
        )
    if media_content.id_or_path == "":  # top level search
        if media_content.type == MediaType.ALBUM:
            result = (
                await master.api.get_albums()
            )  # list of albums with name, artist, uri
        elif media_content.type == MediaType.ARTIST:
            result = await master.api.get_artists()  # list of artists with name, uri
        elif media_content.type == MediaType.GENRE:
            if result := await master.api.get_genres():  # returns list of genre names
                for item in result:
                    # add generated genre uris to list of genre names
                    item["uri"] = create_owntone_uri(
                        MediaType.GENRE, cast(str, item["name"])
                    )
        elif media_content.type == MediaType.PLAYLIST:
            result = (
                await master.api.get_playlists()
            )  # list of playlists with name, uri
        if result is None:
            raise BrowseError(
                f"Media not found for {media_content.type} / {media_content_id}"
            )
        return create_browse_media_response(
            master,
            media_content,
            cast(list[dict[str, int | str]], result),
        )
    # Not a directory or top level of library
    # We should have content type and id
    if media_content.type == MediaType.ALBUM:
        result = await master.api.get_tracks(album_id=media_content.id_or_path)
    elif media_content.type == MediaType.ARTIST:
        result = await master.api.get_albums(artist_id=media_content.id_or_path)
    elif media_content.type == MediaType.GENRE:
        if media_content.subtype in {
            MediaType.ALBUM,
            MediaType.ARTIST,
            MediaType.TRACK,
        }:
            result = await master.api.get_genre(
                media_content.id_or_path, media_type=media_content.subtype
            )
    elif media_content.type == MediaType.PLAYLIST:
        result = await master.api.get_tracks(playlist_id=media_content.id_or_path)

    if result is None:
        raise BrowseError(
            f"Media not found for {media_content.type} / {media_content_id}"
        )

    return create_browse_media_response(
        master, media_content, cast(list[dict[str, int | str]], result)
    )