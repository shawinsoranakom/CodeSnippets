def browse_media(  # noqa: C901
    hass, is_internal, media_content_type, media_content_id, *, platform=None
):
    """Implement the websocket media browsing helper."""
    server_id = None
    plex_server = None
    special_folder = None

    if media_content_id:
        url = URL(media_content_id)
        server_id = url.host
        plex_server = get_plex_server(hass, server_id)
        if media_content_type == "hub":
            _, hub_location, hub_identifier = url.parts
        elif media_content_type in ["library", "server"] and len(url.parts) > 2:
            _, media_content_id, special_folder = url.parts
        else:
            media_content_id = url.name

    if media_content_type in ("plex_root", None):
        return root_payload(hass, is_internal, platform=platform)

    def item_payload(item, short_name=False, extra_params=None):
        """Create response payload for a single media item."""
        try:
            media_class = ITEM_TYPE_MEDIA_CLASS[item.type]
        except KeyError as err:
            raise UnknownMediaType(f"Unknown type received: {item.type}") from err
        payload = {
            "title": pretty_title(item, short_name),
            "media_class": media_class,
            "media_content_id": generate_plex_uri(
                server_id, item.ratingKey, params=extra_params
            ),
            "media_content_type": item.type,
            "can_play": True,
            "can_expand": item.type in EXPANDABLES,
        }
        if hasattr(item, "thumbUrl"):
            plex_server.thumbnail_cache.setdefault(str(item.ratingKey), item.thumbUrl)
            if is_internal:
                thumbnail = item.thumbUrl
            else:
                thumbnail = get_proxy_image_url(
                    server_id,
                    item.ratingKey,
                )
            payload["thumbnail"] = thumbnail

        return BrowseMedia(**payload)

    def server_payload():
        """Create response payload to describe libraries of the Plex server."""
        server_info = BrowseMedia(
            title=plex_server.friendly_name,
            media_class=MediaClass.DIRECTORY,
            media_content_id=generate_plex_uri(server_id, "server"),
            media_content_type="server",
            can_play=False,
            can_expand=True,
            children=[],
            children_media_class=MediaClass.DIRECTORY,
            thumbnail="/api/brands/integration/plex/logo.png",
        )
        if platform != "sonos":
            server_info.children.append(
                special_library_payload(server_info, "Recommended")
            )
        for library in plex_server.library.sections():
            if library.type == "photo":
                continue
            if library.type != "artist" and platform == "sonos":
                continue
            server_info.children.append(library_section_payload(library))
        server_info.children.append(playlists_payload())
        return server_info

    def library_contents(library):
        """Create response payload to describe contents of a specific library."""
        library_info = library_section_payload(library)
        library_info.children = [special_library_payload(library_info, "Recommended")]
        for item in library.all():
            try:
                library_info.children.append(item_payload(item))
            except UnknownMediaType:
                continue
        return library_info

    def playlists_payload():
        """Create response payload for all available playlists."""
        playlists_info = {
            "title": "Playlists",
            "media_class": MediaClass.DIRECTORY,
            "media_content_id": generate_plex_uri(server_id, "all"),
            "media_content_type": "playlists",
            "can_play": False,
            "can_expand": True,
            "children": [],
        }
        for playlist in plex_server.playlists():
            if (
                playlist.type != "directory"
                and playlist.playlistType != "audio"
                and platform == "sonos"
            ):
                continue
            try:
                playlists_info["children"].append(item_payload(playlist))
            except UnknownMediaType:
                continue
        response = BrowseMedia(**playlists_info)
        response.children_media_class = MediaClass.PLAYLIST
        return response

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

    if media_content_type == "hub":
        if hub_location == "server":
            hub = next(
                x
                for x in plex_server.library.hubs()
                if x.hubIdentifier == hub_identifier
            )
            media_content_id = f"server/{hub.hubIdentifier}"
        else:
            library_section = plex_server.library.sectionByID(int(hub_location))
            hub = next(
                x for x in library_section.hubs() if x.hubIdentifier == hub_identifier
            )
            media_content_id = f"{hub.librarySectionID}/{hub.hubIdentifier}"
        try:
            children_media_class = ITEM_TYPE_MEDIA_CLASS[hub.type]
        except KeyError as err:
            raise UnknownMediaType(f"Unknown type received: {hub.type}") from err
        payload = {
            "title": hub.title,
            "media_class": MediaClass.DIRECTORY,
            "media_content_id": generate_plex_uri(server_id, media_content_id),
            "media_content_type": "hub",
            "can_play": False,
            "can_expand": True,
            "children": [],
            "children_media_class": children_media_class,
        }
        for item in hub.items:
            if hub.type == "station":
                if platform == "sonos":
                    continue
                payload["children"].append(station_payload(item))
            else:
                extra_params = None
                hub_context = hub.context.split(".")[-1]
                if hub_context in ("continue", "inprogress", "ondeck"):
                    extra_params = {"resume": 1}
                payload["children"].append(
                    item_payload(item, extra_params=extra_params)
                )
        return BrowseMedia(**payload)

    if special_folder:
        if media_content_type == "server":
            library_or_section = plex_server.library
            children_media_class = MediaClass.DIRECTORY
            title = plex_server.friendly_name
        elif media_content_type == "library":
            library_or_section = plex_server.library.sectionByID(int(media_content_id))
            title = library_or_section.title
            try:
                children_media_class = ITEM_TYPE_MEDIA_CLASS[library_or_section.TYPE]
            except KeyError as err:
                raise UnknownMediaType(
                    f"Unknown type received: {library_or_section.TYPE}"
                ) from err
        else:
            raise BrowseError(
                f"Media not found: {media_content_type} / {media_content_id}"
            )

        payload = {
            "title": title,
            "media_class": MediaClass.DIRECTORY,
            "media_content_id": generate_plex_uri(
                server_id, f"{media_content_id}/{special_folder}"
            ),
            "media_content_type": media_content_type,
            "can_play": False,
            "can_expand": True,
            "children": [],
            "children_media_class": children_media_class,
        }

        if special_folder == "Recommended":
            for item in library_or_section.hubs():
                if item.type == "photo":
                    continue
                payload["children"].append(hub_payload(item))

        return BrowseMedia(**payload)

    try:
        if media_content_type == "server":
            return server_payload()

        if media_content_type == "library":
            library_id = int(media_content_id)
            library = plex_server.library.sectionByID(library_id)
            return library_contents(library)

    except UnknownMediaType as err:
        raise BrowseError(
            f"Media not found: {media_content_type} / {media_content_id}"
        ) from err

    if media_content_type == "playlists":
        return playlists_payload()

    payload = {
        "media_type": DOMAIN,
        "plex_key": int(media_content_id),
    }
    response = build_item_response(payload)
    if response is None:
        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")
    return response