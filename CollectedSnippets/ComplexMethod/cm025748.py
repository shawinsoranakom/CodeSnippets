async def guess_hardware_owners(
    hass: HomeAssistant, device_path: str
) -> list[FirmwareInfo]:
    """Guess the firmware info based on installed addons and other integrations."""
    device_guesses: defaultdict[str, list[FirmwareInfo]] = defaultdict(list)

    async for firmware_info in hass.data[DATA_COMPONENT].iter_firmware_info():
        device_guesses[firmware_info.device].append(firmware_info)

    if not is_hassio(hass):
        return device_guesses.get(device_path, [])

    # It may be possible for the OTBR addon to be present without the integration
    otbr_addon_manager = get_otbr_addon_manager(hass)
    otbr_addon_fw_info = await get_otbr_addon_firmware_info(hass, otbr_addon_manager)
    otbr_path = otbr_addon_fw_info.device if otbr_addon_fw_info is not None else None

    # Only create a new entry if there are no existing OTBR ones
    if otbr_path is not None and not any(
        info.source == "otbr" for info in device_guesses[otbr_path]
    ):
        assert otbr_addon_fw_info is not None
        device_guesses[otbr_path].append(otbr_addon_fw_info)

    multipan_addon_manager = await get_multiprotocol_addon_manager(hass)

    try:
        multipan_addon_info = await multipan_addon_manager.async_get_addon_info()
    except AddonError:
        pass
    else:
        if multipan_addon_info.state != AddonState.NOT_INSTALLED:
            multipan_path = multipan_addon_info.options.get("device")

            if multipan_path is not None:
                device_guesses[multipan_path].append(
                    FirmwareInfo(
                        device=multipan_path,
                        firmware_type=ApplicationType.CPC,
                        firmware_version=None,
                        source="multiprotocol",
                        owners=[OwningAddon(slug=multipan_addon_manager.addon_slug)],
                    )
                )

    # Z2M can be provided by one of many add-ons, we match them by name
    for app_info in get_apps_list(hass) or []:
        slug = app_info.get("slug")

        if not isinstance(slug, str) or Z2M_ADDON_SLUG_REGEX.fullmatch(slug) is None:
            continue

        z2m_addon_manager = get_z2m_addon_manager(hass, slug)
        z2m_fw_info = await get_z2m_addon_firmware_info(hass, z2m_addon_manager)

        if z2m_fw_info is not None:
            device_guesses[z2m_fw_info.device].append(z2m_fw_info)

    return device_guesses.get(device_path, [])