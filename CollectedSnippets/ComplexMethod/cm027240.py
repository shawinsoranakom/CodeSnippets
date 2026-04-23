async def build_item_response(
    entity: SqueezeBoxMediaPlayerEntity,
    player: Player,
    payload: dict[str, str | None],
    browse_limit: int,
    browse_data: BrowseData,
) -> BrowseMedia:
    """Create response payload for search described by payload."""

    internal_request = is_internal_request(entity.hass)

    search_id = payload["search_id"]
    search_type = payload["search_type"]
    search_query = payload.get("search_query")
    assert (
        search_type is not None
    )  # async_browse_media will not call this function if search_type is None
    media_class = browse_data.content_type_media_class[search_type]

    children = None

    if search_id and search_id != search_type:
        browse_id = (browse_data.squeezebox_id_by_type[search_type], search_id)
    else:
        browse_id = None

    result = await player.async_browse(
        browse_data.media_type_to_squeezebox[search_type],
        limit=browse_limit,
        browse_id=browse_id,
        search_query=search_query,
    )

    if result is not None and result.get("items"):
        item_type = browse_data.content_type_to_child_type[search_type]

        children = []
        for item in result["items"]:
            # Force the item id to a string in case it's numeric from some lms
            item["id"] = str(item.get("id", ""))
            if search_type in ["favorites", "favorite"]:
                child_media = _build_response_favorites(item)

            elif search_type in ["apps", "radios"]:
                # item["cmd"] contains the name of the command to use with the cli for the app
                # add the command to the dictionaries
                if item["title"] == "Search" or item.get("type") in UNPLAYABLE_TYPES:
                    # Skip searches in apps as they'd need UI or if the link isn't to audio
                    continue
                app_cmd = "app-" + item["cmd"]

                if app_cmd not in browse_data.known_apps_radios:
                    browse_data.add_new_command(app_cmd, "item_id")

                child_media = _build_response_apps_radios_category(
                    browse_data=browse_data, cmd=app_cmd, item=item
                )

            elif search_type in browse_data.known_apps_radios:
                if (
                    item.get("title") in ["Search", None]
                    or item.get("type") in UNPLAYABLE_TYPES
                ):
                    # Skip searches in apps as they'd need UI
                    continue

                child_media = _build_response_known_app(browse_data, search_type, item)

            elif item_type:
                child_media = BrowseMedia(
                    media_content_id=item["id"],
                    title=item["title"],
                    media_content_type=item_type,
                    media_class=CONTENT_TYPE_MEDIA_CLASS[item_type]["item"],
                    can_expand=bool(CONTENT_TYPE_MEDIA_CLASS[item_type]["children"]),
                    can_play=True,
                )

            assert child_media.media_class is not None

            child_media.thumbnail = _get_item_thumbnail(
                item=item,
                player=player,
                entity=entity,
                item_type=item_type,
                search_type=search_type,
                internal_request=internal_request,
                known_apps_radios=browse_data.known_apps_radios,
            )

            children.append(child_media)

    if children is None:
        raise BrowseError(
            translation_domain=DOMAIN,
            translation_key="browse_media_not_found",
            translation_placeholders={
                "type": str(search_type),
                "id": str(search_id),
            },
        )

    assert media_class["item"] is not None
    if not search_id:
        search_id = search_type

    return BrowseMedia(
        title=result.get("title"),
        media_class=media_class["item"],
        children_media_class=media_class["children"],
        media_content_id=search_id,
        media_content_type=search_type,
        can_play=any(child.can_play for child in children),
        children=children,
        can_expand=True,
    )