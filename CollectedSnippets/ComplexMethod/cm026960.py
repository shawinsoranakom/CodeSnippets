async def async_ensure_addon_running(
    hass: HomeAssistant, entry: ZwaveJSConfigEntry
) -> None:
    """Ensure that Z-Wave JS add-on is installed and running."""
    addon_manager = _get_addon_manager(hass)
    try:
        addon_info = await addon_manager.async_get_addon_info()
    except AddonError as err:
        raise ConfigEntryNotReady(err) from err

    addon_has_lr = (
        addon_info.version and AwesomeVersion(addon_info.version) >= LR_ADDON_VERSION
    )
    addon_has_esphome = (
        addon_info.version
        and AwesomeVersion(addon_info.version) >= ESPHOME_ADDON_VERSION
    )

    usb_path: str | None = entry.data[CONF_USB_PATH]
    socket_path: str | None = entry.data.get(CONF_SOCKET_PATH)
    # s0_legacy_key was saved as network_key before s2 was added.
    s0_legacy_key: str = entry.data.get(CONF_S0_LEGACY_KEY, "")
    if not s0_legacy_key:
        s0_legacy_key = entry.data.get(CONF_NETWORK_KEY, "")
    s2_access_control_key: str = entry.data.get(CONF_S2_ACCESS_CONTROL_KEY, "")
    s2_authenticated_key: str = entry.data.get(CONF_S2_AUTHENTICATED_KEY, "")
    s2_unauthenticated_key: str = entry.data.get(CONF_S2_UNAUTHENTICATED_KEY, "")
    lr_s2_access_control_key: str = entry.data.get(CONF_LR_S2_ACCESS_CONTROL_KEY, "")
    lr_s2_authenticated_key: str = entry.data.get(CONF_LR_S2_AUTHENTICATED_KEY, "")
    addon_state = addon_info.state
    addon_config = {
        CONF_ADDON_S0_LEGACY_KEY: s0_legacy_key,
        CONF_ADDON_S2_ACCESS_CONTROL_KEY: s2_access_control_key,
        CONF_ADDON_S2_AUTHENTICATED_KEY: s2_authenticated_key,
        CONF_ADDON_S2_UNAUTHENTICATED_KEY: s2_unauthenticated_key,
    }
    if usb_path is not None:
        addon_config[CONF_ADDON_DEVICE] = usb_path
    if addon_has_lr:
        addon_config[CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY] = lr_s2_access_control_key
        addon_config[CONF_ADDON_LR_S2_AUTHENTICATED_KEY] = lr_s2_authenticated_key
    if addon_has_esphome and socket_path is not None:
        addon_config[CONF_ADDON_SOCKET] = socket_path

    if addon_state == AddonState.NOT_INSTALLED:
        addon_manager.async_schedule_install_setup_addon(
            addon_config,
            catch_error=True,
        )
        raise ConfigEntryNotReady

    if addon_state == AddonState.NOT_RUNNING:
        addon_manager.async_schedule_setup_addon(
            addon_config,
            catch_error=True,
        )
        raise ConfigEntryNotReady

    addon_options = addon_info.options
    addon_device = addon_options.get(CONF_ADDON_DEVICE)
    # s0_legacy_key was saved as network_key before s2 was added.
    addon_s0_legacy_key = addon_options.get(CONF_ADDON_S0_LEGACY_KEY, "")
    if not addon_s0_legacy_key:
        addon_s0_legacy_key = addon_options.get(CONF_ADDON_NETWORK_KEY, "")
    addon_s2_access_control_key = addon_options.get(
        CONF_ADDON_S2_ACCESS_CONTROL_KEY, ""
    )
    addon_s2_authenticated_key = addon_options.get(CONF_ADDON_S2_AUTHENTICATED_KEY, "")
    addon_s2_unauthenticated_key = addon_options.get(
        CONF_ADDON_S2_UNAUTHENTICATED_KEY, ""
    )
    updates = {}
    if usb_path != addon_device:
        updates[CONF_USB_PATH] = addon_device
    if s0_legacy_key != addon_s0_legacy_key:
        updates[CONF_S0_LEGACY_KEY] = addon_s0_legacy_key
    if s2_access_control_key != addon_s2_access_control_key:
        updates[CONF_S2_ACCESS_CONTROL_KEY] = addon_s2_access_control_key
    if s2_authenticated_key != addon_s2_authenticated_key:
        updates[CONF_S2_AUTHENTICATED_KEY] = addon_s2_authenticated_key
    if s2_unauthenticated_key != addon_s2_unauthenticated_key:
        updates[CONF_S2_UNAUTHENTICATED_KEY] = addon_s2_unauthenticated_key

    if addon_has_lr:
        addon_lr_s2_access_control_key = addon_options.get(
            CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY, ""
        )
        addon_lr_s2_authenticated_key = addon_options.get(
            CONF_ADDON_LR_S2_AUTHENTICATED_KEY, ""
        )
        if lr_s2_access_control_key != addon_lr_s2_access_control_key:
            updates[CONF_LR_S2_ACCESS_CONTROL_KEY] = addon_lr_s2_access_control_key
        if lr_s2_authenticated_key != addon_lr_s2_authenticated_key:
            updates[CONF_LR_S2_AUTHENTICATED_KEY] = addon_lr_s2_authenticated_key

    if addon_has_esphome:
        addon_socket = addon_options.get(CONF_ADDON_SOCKET)
        if socket_path != addon_socket:
            updates[CONF_SOCKET_PATH] = addon_socket

    if updates:
        hass.config_entries.async_update_entry(entry, data={**entry.data, **updates})