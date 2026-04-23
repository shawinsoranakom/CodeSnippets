async def _async_upload_image(call: ServiceCall) -> None:
    """Handle the upload_image service call."""
    entry = _get_entry_for_device(call)
    address = entry.unique_id
    assert address is not None

    image_data: dict[str, Any] = call.data[ATTR_IMAGE]
    rotation: Rotation = call.data[ATTR_ROTATION]
    dither_mode: DitherMode = call.data[ATTR_DITHER_MODE]
    refresh_mode: RefreshMode = call.data[ATTR_REFRESH_MODE]
    fit_mode: FitMode = call.data[ATTR_FIT_MODE]
    tone_compression_pct: float | None = call.data.get(ATTR_TONE_COMPRESSION)
    tone_compression: float | str = (
        tone_compression_pct / 100.0 if tone_compression_pct is not None else "auto"
    )

    ble_device = async_ble_device_from_address(call.hass, address, connectable=True)
    if ble_device is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
            translation_placeholders={"address": address},
        )

    current = asyncio.current_task()
    if (prev := entry.runtime_data.upload_task) is not None and not prev.done():
        prev.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await prev
    entry.runtime_data.upload_task = current

    try:
        media = await async_resolve_media(
            call.hass, image_data["media_content_id"], None
        )

        if media.path is not None:
            pil_image = await call.hass.async_add_executor_job(
                _load_image, str(media.path)
            )
        else:
            pil_image = await _async_download_image(call.hass, media.url)

        raw_key = entry.data.get(CONF_ENCRYPTION_KEY)
        if raw_key is not None and len(raw_key) != 32:
            entry.async_start_reauth(call.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="authentication_error"
            )
        try:
            encryption_key = bytes.fromhex(raw_key) if raw_key is not None else None
        except ValueError as err:
            entry.async_start_reauth(call.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="authentication_error"
            ) from err

        async with OpenDisplayDevice(
            mac_address=address,
            ble_device=ble_device,
            config=entry.runtime_data.device_config,
            encryption_key=encryption_key,
        ) as device:
            await device.upload_image(
                pil_image,
                refresh_mode=refresh_mode,
                dither_mode=dither_mode,
                tone_compression=tone_compression,
                fit=fit_mode,
                rotate=rotation,
            )
    except asyncio.CancelledError:
        return
    except (AuthenticationFailedError, AuthenticationRequiredError) as err:
        entry.async_start_reauth(call.hass)
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="authentication_error"
        ) from err
    except OpenDisplayError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="upload_error"
        ) from err
    finally:
        if entry.runtime_data.upload_task is current:
            entry.runtime_data.upload_task = None