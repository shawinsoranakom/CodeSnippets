async def handle_get_library(call: ServiceCall) -> ServiceResponse:
    """Handle get_library action."""
    mass = get_music_assistant_client(call.hass, call.data[ATTR_CONFIG_ENTRY_ID])
    media_type = call.data[ATTR_MEDIA_TYPE]
    limit = call.data.get(ATTR_LIMIT, DEFAULT_LIMIT)
    offset = call.data.get(ATTR_OFFSET, DEFAULT_OFFSET)
    order_by = call.data.get(ATTR_ORDER_BY, DEFAULT_SORT_ORDER)
    base_params = {
        "favorite": call.data.get(ATTR_FAVORITE),
        "search": call.data.get(ATTR_SEARCH),
        "limit": limit,
        "offset": offset,
        "order_by": order_by,
    }
    library_result: (
        list[Album]
        | list[Artist]
        | list[Track]
        | list[Radio]
        | list[Playlist]
        | list[Audiobook]
        | list[Podcast]
    )
    if media_type == MediaType.ALBUM:
        library_result = await mass.music.get_library_albums(
            **base_params,
            album_types=call.data.get(ATTR_ALBUM_TYPE),
        )
    elif media_type == MediaType.ARTIST:
        library_result = await mass.music.get_library_artists(
            **base_params,
            album_artists_only=bool(call.data.get(ATTR_ALBUM_ARTISTS_ONLY)),
        )
    elif media_type == MediaType.TRACK:
        library_result = await mass.music.get_library_tracks(
            **base_params,
        )
    elif media_type == MediaType.RADIO:
        library_result = await mass.music.get_library_radios(
            **base_params,
        )
    elif media_type == MediaType.PLAYLIST:
        library_result = await mass.music.get_library_playlists(
            **base_params,
        )
    elif media_type == MediaType.AUDIOBOOK:
        library_result = await mass.music.get_library_audiobooks(
            **base_params,
        )
    elif media_type == MediaType.PODCAST:
        library_result = await mass.music.get_library_podcasts(
            **base_params,
        )
    else:
        raise ServiceValidationError(f"Unsupported media type {media_type}")

    response: ServiceResponse = LIBRARY_RESULTS_SCHEMA(
        {
            ATTR_ITEMS: [
                media_item_dict_from_mass_item(mass, item) for item in library_result
            ],
            ATTR_LIMIT: limit,
            ATTR_OFFSET: offset,
            ATTR_ORDER_BY: order_by,
            ATTR_MEDIA_TYPE: media_type,
        }
    )
    return response