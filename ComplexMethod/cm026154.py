async def _async_snapshot_payload(hass: HomeAssistant) -> dict:  # noqa: C901
    """Return detailed information about entities and devices for a snapshot."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    integration_inputs: dict[str, tuple[list[str], list[str]]] = {}
    integration_configs: dict[str, AnalyticsModifications] = {}

    removed_devices: set[str] = set()

    # Get device list
    for device_entry in dev_reg.devices.values():
        if not device_entry.primary_config_entry:
            continue

        config_entry = hass.config_entries.async_get_entry(
            device_entry.primary_config_entry
        )

        if config_entry is None:
            continue

        if device_entry.entry_type is dr.DeviceEntryType.SERVICE:
            removed_devices.add(device_entry.id)
            continue

        integration_domain = config_entry.domain

        integration_input = integration_inputs.setdefault(integration_domain, ([], []))
        integration_input[0].append(device_entry.id)

    # Get entity list
    for entity_entry in ent_reg.entities.values():
        integration_domain = entity_entry.platform

        integration_input = integration_inputs.setdefault(integration_domain, ([], []))
        integration_input[1].append(entity_entry.entity_id)

    integrations = {
        domain: integration
        for domain, integration in (
            await async_get_integrations(hass, integration_inputs.keys())
        ).items()
        if isinstance(integration, Integration)
    }

    # Filter out custom integrations and integrations that are not device or hub type
    integration_inputs = {
        domain: integration_info
        for domain, integration_info in integration_inputs.items()
        if (integration := integrations.get(domain)) is not None
        and integration.is_built_in
        and integration.manifest.get("integration_type") in ("device", "hub")
    }

    # Call integrations that implement the analytics platform
    for integration_domain, integration_input in integration_inputs.items():
        if (
            modifier := await _async_get_modifier(hass, integration_domain)
        ) is not None:
            try:
                integration_config = await modifier(
                    hass, AnalyticsInput(*integration_input)
                )
            except Exception as err:  # noqa: BLE001
                LOGGER.exception(
                    "Calling async_modify_analytics for integration '%s' failed: %s",
                    integration_domain,
                    err,
                )
                integration_configs[integration_domain] = AnalyticsModifications(
                    remove=True
                )
                continue

            if not isinstance(integration_config, AnalyticsModifications):
                LOGGER.error(  # type: ignore[unreachable]
                    "Calling async_modify_analytics for integration '%s' did not return an AnalyticsConfig",
                    integration_domain,
                )
                integration_configs[integration_domain] = AnalyticsModifications(
                    remove=True
                )
                continue

            integration_configs[integration_domain] = integration_config

    integrations_info: dict[str, dict[str, Any]] = {}

    # We need to refer to other devices, for example in `via_device` field.
    # We don't however send the original device ids outside of Home Assistant,
    # instead we refer to devices by (integration_domain, index_in_integration_device_list).
    device_id_mapping: dict[str, tuple[str, int]] = {}

    # Fill out information about devices
    for integration_domain, integration_input in integration_inputs.items():
        integration_config = integration_configs.get(
            integration_domain, DEFAULT_ANALYTICS_CONFIG
        )

        if integration_config.remove:
            continue

        integration_info = integrations_info.setdefault(
            integration_domain, {"devices": [], "entities": []}
        )

        devices_info = integration_info["devices"]

        for device_id in integration_input[0]:
            device_config = DEFAULT_DEVICE_ANALYTICS_CONFIG
            if integration_config.devices is not None:
                device_config = integration_config.devices.get(device_id, device_config)

            if device_config.remove:
                removed_devices.add(device_id)
                continue

            device_entry = dev_reg.devices[device_id]

            device_id_mapping[device_id] = (integration_domain, len(devices_info))

            devices_info.append(
                {
                    "entry_type": device_entry.entry_type,
                    "has_configuration_url": device_entry.configuration_url is not None,
                    "hw_version": device_entry.hw_version,
                    "manufacturer": device_entry.manufacturer,
                    "model": device_entry.model,
                    "model_id": device_entry.model_id,
                    "sw_version": device_entry.sw_version,
                    "via_device": device_entry.via_device_id,
                    "entities": [],
                }
            )

    # Fill out via_device with new device ids
    for integration_info in integrations_info.values():
        for device_info in integration_info["devices"]:
            if device_info["via_device"] is None:
                continue
            device_info["via_device"] = device_id_mapping.get(device_info["via_device"])

    # Fill out information about entities
    for integration_domain, integration_input in integration_inputs.items():
        integration_config = integration_configs.get(
            integration_domain, DEFAULT_ANALYTICS_CONFIG
        )

        if integration_config.remove:
            continue

        integration_info = integrations_info.setdefault(
            integration_domain, {"devices": [], "entities": []}
        )

        devices_info = integration_info["devices"]
        entities_info = integration_info["entities"]

        for entity_id in integration_input[1]:
            entity_config = DEFAULT_ENTITY_ANALYTICS_CONFIG
            if integration_config.entities is not None:
                entity_config = integration_config.entities.get(
                    entity_id, entity_config
                )

            if entity_config.remove:
                continue

            entity_entry = ent_reg.entities[entity_id]

            entity_state = hass.states.get(entity_id)

            entity_info = {
                # LIMITATION: `assumed_state` can be overridden by users;
                # we should replace it with the original value in the future.
                # It is also not present, if entity is not in the state machine,
                # which can happen for disabled entities.
                "assumed_state": (
                    entity_state.attributes.get(ATTR_ASSUMED_STATE, False)
                    if entity_state is not None
                    else None
                ),
                "domain": entity_entry.domain,
                "entity_category": entity_entry.entity_category,
                "has_entity_name": entity_entry.has_entity_name,
                "original_device_class": entity_entry.original_device_class,
                # LIMITATION: `unit_of_measurement` can be overridden by users;
                # we should replace it with the original value in the future.
                "unit_of_measurement": entity_entry.unit_of_measurement,
            }

            if (device_id_ := entity_entry.device_id) is not None:
                if device_id_ in removed_devices:
                    # The device was removed, so we remove the entity too
                    continue

                if (
                    new_device_id := device_id_mapping.get(device_id_)
                ) is not None and (new_device_id[0] == integration_domain):
                    device_info = devices_info[new_device_id[1]]
                    device_info["entities"].append(entity_info)
                    continue

            entities_info.append(entity_info)

    return integrations_info