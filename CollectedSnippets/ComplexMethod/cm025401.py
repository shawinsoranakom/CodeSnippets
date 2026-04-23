def build_setup_functions(
    hass: HomeAssistant,
    entry: RoborockConfigEntry,
    devices: list[RoborockDevice],
    user_data: UserData,
) -> list[
    Coroutine[
        Any,
        Any,
        RoborockDataUpdateCoordinator
        | RoborockDataUpdateCoordinatorA01
        | RoborockDataUpdateCoordinatorB01
        | RoborockB01Q10UpdateCoordinator
        | None,
    ]
]:
    """Create a list of setup functions that can later be called asynchronously."""
    coordinators: list[
        RoborockDataUpdateCoordinator
        | RoborockDataUpdateCoordinatorA01
        | RoborockDataUpdateCoordinatorB01
        | RoborockB01Q10UpdateCoordinator
    ] = []
    for device in devices:
        _LOGGER.debug("Creating device %s: %s", device.name, device)
        if device.v1_properties is not None:
            coordinators.append(
                RoborockDataUpdateCoordinator(hass, entry, device, device.v1_properties)
            )
        elif device.dyad is not None:
            coordinators.append(
                RoborockWetDryVacUpdateCoordinator(hass, entry, device, device.dyad)
            )
        elif device.zeo is not None:
            coordinators.append(
                RoborockWashingMachineUpdateCoordinator(hass, entry, device, device.zeo)
            )
        elif device.b01_q7_properties is not None:
            coordinators.append(
                RoborockB01Q7UpdateCoordinator(
                    hass, entry, device, device.b01_q7_properties
                )
            )
        elif device.b01_q10_properties is not None:
            coordinators.append(
                RoborockB01Q10UpdateCoordinator(
                    hass, entry, device, device.b01_q10_properties
                )
            )
        else:
            _LOGGER.warning(
                "Not adding device %s because its protocol version %s or category %s is not supported",
                device.duid,
                device.device_info.pv,
                device.product.category.name,
            )

    return [setup_coordinator(coordinator) for coordinator in coordinators]