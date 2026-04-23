def _item_to_media_class(item, parent_item=None):
    if "type" not in item:
        return MediaClass.DIRECTORY
    if item["type"] in ("webradio", "mywebradio"):
        return MediaClass.CHANNEL
    if item["type"] in ("song", "cuesong"):
        return MediaClass.TRACK
    if item.get("artist"):
        return MediaClass.ALBUM
    if item["uri"].startswith(ARTISTS_URI_PREFIX) and len(item["uri"]) > len(
        ARTISTS_URI_PREFIX
    ):
        return MediaClass.ARTIST
    if parent_item:
        return _item_to_children_media_class(parent_item)
    return MediaClass.DIRECTORY