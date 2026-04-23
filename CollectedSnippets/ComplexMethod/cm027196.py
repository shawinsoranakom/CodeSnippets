def _item_to_children_media_class(item, info=None):
    if info and "album" in info and "artist" in info:
        return MediaClass.TRACK
    if item["uri"].startswith(PLAYLISTS_URI_PREFIX):
        return MediaClass.PLAYLIST
    if item["uri"].startswith(ARTISTS_URI_PREFIX):
        if len(item["uri"]) > len(ARTISTS_URI_PREFIX):
            return MediaClass.ALBUM
        return MediaClass.ARTIST
    if item["uri"].startswith(ALBUMS_URI_PREFIX):
        if len(item["uri"]) > len(ALBUMS_URI_PREFIX):
            return MediaClass.TRACK
        return MediaClass.ALBUM
    if item["uri"].startswith(GENRES_URI_PREFIX):
        if len(item["uri"]) > len(GENRES_URI_PREFIX):
            return MediaClass.ALBUM
        return MediaClass.GENRE
    if item["uri"].startswith(LAST_100_URI_PREFIX) or item["uri"] == FAVOURITES_URI:
        return MediaClass.TRACK
    if item["uri"].startswith(RADIO_URI_PREFIX):
        return MediaClass.CHANNEL
    return MediaClass.DIRECTORY