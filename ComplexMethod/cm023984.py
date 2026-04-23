async def mock_async_browse(
    media_type: MediaType,
    limit: int,
    browse_id: tuple | None = None,
    search_query: str | None = None,
) -> dict | None:
    """Mock the async_browse method of pysqueezebox.Player."""
    child_types = {
        "favorites": "favorites",
        "favorite": "favorite",
        "new music": "album",
        "album artists": "artists",
        "albums": "album",
        "album": "track",
        "genres": "genre",
        "genre": "album",
        "artists": "artist",
        "artist": "album",
        "titles": "title",
        "title": "title",
        "playlists": "playlist",
        "playlist": "title",
        "apps": "app",
        "radios": "app",
        "app-fakecommand": "track",
    }
    fake_items = [
        {
            "title": "Fake Item 1",
            "id": FAKE_VALID_ITEM_ID,
            "hasitems": False,
            "isaudio": True,
            "item_type": child_types[media_type],
            "artwork_track_id": "b35bb9e9",
            "url": "file:///var/lib/squeezeboxserver/music/track_1.mp3",
            "cmd": "fakecommand",
            "icon": "plugins/Qobuz/html/images/qobuz.png",
        },
        {
            "title": "Fake Item 2",
            "id": FAKE_VALID_ITEM_ID + "_2",
            "hasitems": media_type == "favorites",
            "isaudio": False,
            "item_type": child_types[media_type],
            "image_url": "http://lms.internal:9000/html/images/favorites.png",
            "url": "file:///var/lib/squeezeboxserver/music/track_2.mp3",
            "cmd": "fakecommand",
            "icon": "plugins/Qobuz/html/images/qobuz.png",
        },
        {
            "title": "Fake Item 3",
            "id": FAKE_VALID_ITEM_ID + "_3",
            "hasitems": media_type == "favorites",
            "isaudio": True,
            "album_id": FAKE_VALID_ITEM_ID if media_type == "favorites" else None,
            "url": "file:///var/lib/squeezeboxserver/music/track_3.mp3",
            "cmd": "fakecommand",
            "icon": "plugins/Qobuz/html/images/qobuz.png",
        },
        {
            "title": "Fake Invalid Item 1",
            "id": FAKE_VALID_ITEM_ID + "invalid_3",
            "hasitems": media_type == "favorites",
            "isaudio": True,
            "album_id": FAKE_VALID_ITEM_ID if media_type == "favorites" else None,
            "url": "file:///var/lib/squeezeboxserver/music/track_3.mp3",
            "cmd": "fakecommand",
            "icon": "plugins/Qobuz/html/images/qobuz.png",
            "type": "text",
        },
    ]

    if browse_id:
        search_type, search_id = browse_id
        if search_id:
            if search_type == "playlist_id":
                return (
                    {
                        "title": "Fake Item 1",
                        "items": fake_items,
                    }
                    if search_id == FAKE_VALID_ITEM_ID
                    else None
                )
            if search_type in SQUEEZEBOX_ID_BY_TYPE.values():
                for item in fake_items:
                    if item["id"] == search_id:
                        return {
                            "title": item["title"],
                            "items": [item],
                        }
            return None
        if search_type in SQUEEZEBOX_ID_BY_TYPE.values():
            return {
                "title": search_type,
                "items": fake_items,
            }
        return None

    if search_query:
        if search_query not in [x["title"] for x in fake_items]:
            return None

        for item in fake_items:
            if (
                item["title"] == search_query
                and item["item_type"] == child_types[media_type]
            ):
                return {
                    "title": media_type,
                    "items": [item],
                }

    if (
        media_type in MEDIA_TYPE_TO_SQUEEZEBOX.values()
        or media_type == "app-fakecommand"
    ):
        return {
            "title": media_type,
            "items": fake_items,
        }
    return None