async def _title(hass: HomeAssistant, discovery_info: HassioServiceInfo) -> str:
    """Return config entry title."""
    device: str | None = None
    addon_manager = get_addon_manager(hass, discovery_info.slug)

    with suppress(AddonError):
        addon_info = await addon_manager.async_get_addon_info()
        device = addon_info.options.get("device")

    if _is_yellow(hass) and device == "/dev/ttyAMA1":
        return f"Home Assistant Yellow ({discovery_info.name})"

    if device and ("Connect_ZBT-1" in device or "SkyConnect" in device):
        return f"Home Assistant Connect ZBT-1 ({discovery_info.name})"

    if device and "Nabu_Casa_ZBT-2" in device:
        return f"Home Assistant Connect ZBT-2 ({discovery_info.name})"

    return discovery_info.name