def _process_search_results(
    mass: MusicAssistantClient,
    search_results: SearchResults,
    media_types: list[MASSMediaType],
) -> list[BrowseMedia]:
    """Process search results into BrowseMedia items."""
    result: list[BrowseMedia] = []

    # Process search results for each media type
    for media_type in media_types:
        # Get items for each media type using pattern matching
        items: list[MediaItemType] = []
        match media_type:
            case MASSMediaType.ARTIST if search_results.artists:
                # Cast to ensure type safety
                items = cast(list[MediaItemType], search_results.artists)
            case MASSMediaType.ALBUM if search_results.albums:
                items = cast(list[MediaItemType], search_results.albums)
            case MASSMediaType.TRACK if search_results.tracks:
                items = cast(list[MediaItemType], search_results.tracks)
            case MASSMediaType.PLAYLIST if search_results.playlists:
                items = cast(list[MediaItemType], search_results.playlists)
            case MASSMediaType.RADIO if search_results.radio:
                items = cast(list[MediaItemType], search_results.radio)
            case MASSMediaType.PODCAST if search_results.podcasts:
                items = cast(list[MediaItemType], search_results.podcasts)
            case MASSMediaType.AUDIOBOOK if search_results.audiobooks:
                items = cast(list[MediaItemType], search_results.audiobooks)
            case _:
                continue

        # Add available items to results
        for item in items:
            if not item.available:
                continue

            # Create browse item
            # Convert to string to get the original value since we're using MASSMediaType enum
            str_media_type = media_type.value.lower()
            can_expand = _should_expand_media_type(str_media_type)
            media_class = _get_media_class_for_type(str_media_type)

            browse_item = build_item(
                mass,
                item,
                can_expand=can_expand,
                media_class=media_class,
            )
            result.append(browse_item)

    return result