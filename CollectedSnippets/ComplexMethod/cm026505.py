async def handle_search(call: ServiceCall) -> ServiceResponse:
    """Handle queue_command action."""
    mass = get_music_assistant_client(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    search_name = call.data[ATTR_SEARCH_NAME]
    search_artist = call.data.get(ATTR_SEARCH_ARTIST)
    search_album = call.data.get(ATTR_SEARCH_ALBUM)
    if search_album and search_artist:
        search_name = f"{search_artist} - {search_album} - {search_name}"
    elif search_album:
        search_name = f"{search_album} - {search_name}"
    elif search_artist:
        search_name = f"{search_artist} - {search_name}"
    search_results = await mass.music.search(
        search_query=search_name,
        media_types=call.data.get(ATTR_MEDIA_TYPE, MediaType.ALL),
        limit=call.data[ATTR_LIMIT],
        library_only=call.data[ATTR_LIBRARY_ONLY],
    )
    response: ServiceResponse = SEARCH_RESULT_SCHEMA(
        {
            ATTR_ARTISTS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.artists
            ],
            ATTR_ALBUMS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.albums
            ],
            ATTR_TRACKS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.tracks
            ],
            ATTR_PLAYLISTS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.playlists
            ],
            ATTR_RADIO: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.radio
            ],
            ATTR_AUDIOBOOKS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.audiobooks
            ],
            ATTR_PODCASTS: [
                media_item_dict_from_mass_item(mass, item)
                for item in search_results.podcasts
            ],
        }
    )
    return response