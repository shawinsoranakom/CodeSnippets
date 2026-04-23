async def async_browse_media(
    hass: HomeAssistant,
    mass: MusicAssistantClient,
    media_content_id: str | None,
    media_content_type: str | None,
) -> BrowseMedia:
    """Browse media."""
    if media_content_id is None:
        return await build_main_listing(hass)

    assert media_content_type is not None

    if media_source.is_media_source_id(media_content_id):
        return await media_source.async_browse_media(
            hass, media_content_id, content_filter=media_source_filter
        )

    if media_content_id == LIBRARY_ARTISTS:
        return await build_artists_listing(mass)
    if media_content_id == LIBRARY_ALBUMS:
        return await build_albums_listing(mass)
    if media_content_id == LIBRARY_TRACKS:
        return await build_tracks_listing(mass)
    if media_content_id == LIBRARY_PLAYLISTS:
        return await build_playlists_listing(mass)
    if media_content_id == LIBRARY_RADIO:
        return await build_radio_listing(mass)
    if media_content_id == LIBRARY_PODCASTS:
        return await build_podcasts_listing(mass)
    if media_content_id == LIBRARY_AUDIOBOOKS:
        return await build_audiobooks_listing(mass)
    if "artist" in media_content_id:
        return await build_artist_items_listing(mass, media_content_id)
    if "album" in media_content_id:
        return await build_album_items_listing(mass, media_content_id)
    if "playlist" in media_content_id:
        return await build_playlist_items_listing(mass, media_content_id)
    raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")