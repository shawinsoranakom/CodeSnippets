def create_browse_media_response(
    master: media_player.ForkedDaapdMaster,
    media_content: MediaContent,
    result: list[dict[str, int | str]],
    children: list[BrowseMedia] | None = None,
) -> BrowseMedia:
    """Convert the results into a browse media response."""
    internal_request = is_internal_request(master.hass)
    if not children:  # Directory searches will pass in subdirectories as children
        children = []
    for item in result:
        if item.get("data_kind") == "spotify" or (
            "path" in item and cast(str, item["path"]).startswith("spotify")
        ):  # Exclude spotify data from OwnTone library
            continue
        assert isinstance(item["uri"], str)
        media_type = OWNTONE_TYPE_TO_MEDIA_TYPE[item["uri"].split(":")[1]]
        title = item.get("name") or item.get("title")  # only tracks use title
        assert isinstance(title, str)
        media_content_id = create_media_content_id(
            title=f"{media_content.title} / {title}",
            owntone_uri=item["uri"],
            subtype=media_content.subtype,
        )
        if artwork := item.get("artwork_url"):
            thumbnail = (
                master.api.full_url(cast(str, artwork))
                if internal_request
                else master.get_browse_image_url(media_type, media_content_id)
            )
        else:
            thumbnail = None
        children.append(
            BrowseMedia(
                title=title,
                media_class=MEDIA_TYPE_TO_MEDIA_CLASS[media_type],
                media_content_id=media_content_id,
                media_content_type=media_type,
                can_play=media_type in CAN_PLAY_TYPE,
                can_expand=media_type in CAN_EXPAND_TYPE,
                thumbnail=thumbnail,
            )
        )
    return BrowseMedia(
        title=media_content.id_or_path
        if media_content.type == MEDIA_TYPE_DIRECTORY
        else media_content.title,
        media_class=MEDIA_TYPE_TO_MEDIA_CLASS[media_content.type],
        media_content_id="",
        media_content_type=media_content.type,
        can_play=media_content.type in CAN_PLAY_TYPE,
        can_expand=media_content.type in CAN_EXPAND_TYPE,
        children=children,
    )