def _setup_services(
    hass: HomeAssistant, entry_data: RuntimeEntryData, services: list[UserService]
) -> None:
    device_info = entry_data.device_info
    if device_info is None:
        # Can happen if device has never connected or .storage cleared
        return
    old_services = entry_data.services.copy()
    to_unregister: list[UserService] = []
    to_register: list[UserService] = []
    for service in services:
        if service.key in old_services:
            # Already exists
            if (matching := old_services.pop(service.key)) != service:
                # Need to re-register
                to_unregister.append(matching)
                to_register.append(service)
        else:
            # New service
            to_register.append(service)

    to_unregister.extend(old_services.values())

    entry_data.services = {serv.key: serv for serv in services}

    for service in to_unregister:
        service_name = build_service_name(device_info, service)
        hass.services.async_remove(DOMAIN, service_name)

    for service in to_register:
        _async_register_service(hass, entry_data, device_info, service)