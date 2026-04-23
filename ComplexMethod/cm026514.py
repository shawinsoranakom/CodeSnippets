def device_info(
    info: DeviceInfoDict | None, unique_id: str, mac: str | None = None
) -> DeviceInfo:
    """Create device info for PoolDose devices."""
    if info is None:
        info = {}

    api_version = (info.get("API_VERSION") or "").removesuffix("/")

    return DeviceInfo(
        identifiers={(DOMAIN, unique_id)},
        manufacturer=MANUFACTURER,
        model=info.get("MODEL") or None,
        model_id=info.get("MODEL_ID") or None,
        name=info.get("NAME") or None,
        serial_number=unique_id,
        sw_version=(
            f"{info.get('FW_VERSION')} (SW v{info.get('SW_VERSION')}, API {api_version})"
            if info.get("FW_VERSION") and info.get("SW_VERSION") and api_version
            else None
        ),
        hw_version=info.get("FW_CODE") or None,
        configuration_url=(
            f"http://{info['IP']}/index.html" if info.get("IP") else None
        ),
        connections={(CONNECTION_NETWORK_MAC, mac)} if mac else set(),
    )