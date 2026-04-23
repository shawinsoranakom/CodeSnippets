async def handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request
) -> Response:
    """Handle webhook callback."""
    if webhook_id in hass.data[DOMAIN][DATA_DELETED_IDS]:
        return Response(status=410)

    config_entry: ConfigEntry = hass.data[DOMAIN][DATA_CONFIG_ENTRIES][webhook_id]

    device_name: str = config_entry.data[ATTR_DEVICE_NAME]

    try:
        req_data = await request.json()
    except ValueError:
        _LOGGER.warning("Received invalid JSON from mobile_app device: %s", device_name)
        return empty_okay_response(status=HTTPStatus.BAD_REQUEST)

    if (
        ATTR_WEBHOOK_ENCRYPTED not in req_data
        and config_entry.data[ATTR_SUPPORTS_ENCRYPTION]
    ):
        _LOGGER.warning(
            "Refusing to accept unencrypted webhook from %s",
            device_name,
        )
        return error_response(ERR_ENCRYPTION_REQUIRED, "Encryption required")

    try:
        req_data = WEBHOOK_PAYLOAD_SCHEMA(req_data)
    except vol.Invalid as ex:
        err = vol.humanize.humanize_error(req_data, ex)
        _LOGGER.error(
            "Received invalid webhook from %s with payload: %s", device_name, err
        )
        return empty_okay_response()

    webhook_type = req_data[ATTR_WEBHOOK_TYPE]

    webhook_payload = None

    if ATTR_WEBHOOK_ENCRYPTED in req_data:
        enc_data = req_data[ATTR_WEBHOOK_ENCRYPTED_DATA]
        try:
            webhook_payload = decrypt_payload(config_entry.data[CONF_SECRET], enc_data)
            if ATTR_NO_LEGACY_ENCRYPTION not in config_entry.data:
                data = {**config_entry.data, ATTR_NO_LEGACY_ENCRYPTION: True}
                hass.config_entries.async_update_entry(config_entry, data=data)
        except CryptoError:
            if ATTR_NO_LEGACY_ENCRYPTION not in config_entry.data:
                try:
                    webhook_payload = decrypt_payload_legacy(
                        config_entry.data[CONF_SECRET], enc_data
                    )
                except CryptoError:
                    _LOGGER.warning(
                        "Ignoring encrypted payload because unable to decrypt"
                    )
                except ValueError:
                    _LOGGER.warning("Ignoring invalid JSON in encrypted payload")
            else:
                _LOGGER.warning("Ignoring encrypted payload because unable to decrypt")
        except ValueError as err:
            _LOGGER.warning("Ignoring invalid JSON in encrypted payload: %s", err)
    else:
        webhook_payload = req_data.get(ATTR_WEBHOOK_DATA, {})

    if webhook_payload is None:
        return empty_okay_response()

    if webhook_type not in WEBHOOK_COMMANDS:
        _LOGGER.error(
            "Received invalid webhook from %s of type: %s", device_name, webhook_type
        )
        return empty_okay_response()

    _LOGGER.debug(
        "Received webhook payload from %s for type %s: %s",
        device_name,
        webhook_type,
        webhook_payload,
    )

    # Shield so we make sure we finish the webhook, even if sender hangs up.
    return await asyncio.shield(
        WEBHOOK_COMMANDS[webhook_type](hass, config_entry, webhook_payload)
    )