def _is_ignored_device(discovery_info: SsdpServiceInfo) -> bool:
    """Return True if this device should be ignored for discovery.

    These devices are supported better by other integrations, so don't bug
    the user about them. The user can add them if desired by via the user config
    flow, which will list all discovered but unconfigured devices.
    """
    # Did the discovery trigger more than just this flow?
    if len(discovery_info.x_homeassistant_matching_domains) > 1:
        LOGGER.debug(
            "Ignoring device supported by multiple integrations: %s",
            discovery_info.x_homeassistant_matching_domains,
        )
        return True

    # Is the root device not a DMR?
    if discovery_info.upnp.get(ATTR_UPNP_DEVICE_TYPE) not in DmrDevice.DEVICE_TYPES:
        return True

    # Special cases for devices with other discovery methods (e.g. mDNS), or
    # that advertise multiple unrelated (sent in separate discovery packets)
    # UPnP devices.
    manufacturer = (discovery_info.upnp.get(ATTR_UPNP_MANUFACTURER) or "").lower()
    model = (discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME) or "").lower()

    if manufacturer.startswith("xbmc") or model == "kodi":
        # kodi
        return True
    if "philips" in manufacturer and "tv" in model:
        # philips_js
        # These TVs don't have a stable UDN, so also get discovered as a new
        # device every time they are turned on.
        return True
    if manufacturer.startswith("samsung") and "tv" in model:
        # samsungtv
        return True
    if manufacturer.startswith("lg") and "tv" in model:
        # webostv
        return True

    return False