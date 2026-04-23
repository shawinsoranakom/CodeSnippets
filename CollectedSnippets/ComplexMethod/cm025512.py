def build_item_response(payload):
        """Create response payload for the provided media query."""
        try:
            media = plex_server.lookup_media(**payload)
        except MediaNotFound:
            return None

        try:
            media_info = item_payload(media)
        except UnknownMediaType:
            return None
        if media_info.can_expand:
            media_info.children = []
            if media.TYPE == "artist" and platform != "sonos":
                if (station := media.station()) is not None:
                    media_info.children.append(station_payload(station))
            for item in media:
                try:
                    media_info.children.append(item_payload(item, short_name=True))
                except UnknownMediaType:
                    continue
        return media_info