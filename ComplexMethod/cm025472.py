async def websocket_remove_media(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remove media."""
    try:
        item = MediaSourceItem.from_uri(hass, msg["media_content_id"], None)
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return

    if item.domain != DOMAIN:
        connection.send_error(
            msg["id"], websocket_api.ERR_INVALID_FORMAT, "Invalid media source domain"
        )
        return

    source = cast(LocalSource, hass.data[MEDIA_SOURCE_DATA][item.domain])

    try:
        await source.async_delete_media(item)
    except Unresolvable as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
    except FileNotFoundError as err:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, str(err))
    except PathNotSupportedError as err:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_SUPPORTED, str(err))
    except OSError as err:
        connection.send_error(msg["id"], websocket_api.ERR_UNKNOWN_ERROR, str(err))
    else:
        connection.send_result(msg["id"])