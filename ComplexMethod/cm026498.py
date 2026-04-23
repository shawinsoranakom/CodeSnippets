def _get_media_types_from_query(query: SearchMediaQuery) -> list[MASSMediaType]:
    """Map query to Music Assistant media types."""
    media_types: list[MASSMediaType] = []

    match query.media_content_type:
        case MediaType.ARTIST:
            media_types = [MASSMediaType.ARTIST]
        case MediaType.ALBUM:
            media_types = [MASSMediaType.ALBUM]
        case MediaType.TRACK:
            media_types = [MASSMediaType.TRACK]
        case MediaType.PLAYLIST:
            media_types = [MASSMediaType.PLAYLIST]
        case "radio":
            media_types = [MASSMediaType.RADIO]
        case "audiobook":
            media_types = [MASSMediaType.AUDIOBOOK]
        case MediaType.PODCAST:
            media_types = [MASSMediaType.PODCAST]
        case _:
            # No specific type selected
            if query.media_filter_classes:
                # Map MediaClass to search types
                mapping = {
                    MediaClass.ARTIST: MASSMediaType.ARTIST,
                    MediaClass.ALBUM: MASSMediaType.ALBUM,
                    MediaClass.TRACK: MASSMediaType.TRACK,
                    MediaClass.PLAYLIST: MASSMediaType.PLAYLIST,
                    MediaClass.MUSIC: MASSMediaType.RADIO,
                    MediaClass.DIRECTORY: MASSMediaType.AUDIOBOOK,
                    MediaClass.PODCAST: MASSMediaType.PODCAST,
                }
                media_types = [
                    mapping[cls] for cls in query.media_filter_classes if cls in mapping
                ]

    # Default to all types if none specified
    if not media_types:
        media_types = [
            MASSMediaType.ARTIST,
            MASSMediaType.ALBUM,
            MASSMediaType.TRACK,
            MASSMediaType.PLAYLIST,
            MASSMediaType.RADIO,
            MASSMediaType.AUDIOBOOK,
            MASSMediaType.PODCAST,
        ]

    return media_types