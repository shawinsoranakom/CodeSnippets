def _migrate_device_identifiers(
    entry: TouchlineSLConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Migrate zone device identifiers from zone-only to module-aware format.

    Previously, zone devices used (DOMAIN, str(zone_id)) as their identifier.
    This caused collisions when multiple modules had zones with the same ID.
    The new format is (DOMAIN, f"{module_id}-{zone_id}").
    """
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        for identifier_domain, identifier in device.identifiers:
            if identifier_domain != DOMAIN:
                continue
            # Skip identifiers that already include a module prefix (new format)
            if "-" in identifier:
                continue

            # Resolve the module device via via_device_id
            if device.via_device_id is None:
                break

            module_device = device_registry.async_get(device.via_device_id)
            if module_device is None:
                break

            module_id: str | None = None
            for module_domain, module_identifier in module_device.identifiers:
                if module_domain == DOMAIN:
                    module_id = module_identifier
                    break

            if module_id is None:
                break

            # Preserve other identifiers and replace only the legacy one
            updated_identifiers = set(device.identifiers)
            updated_identifiers.discard((DOMAIN, identifier))
            updated_identifiers.add((DOMAIN, f"{module_id}-{identifier}"))
            device_registry.async_update_device(
                device.id,
                new_identifiers=updated_identifiers,
            )
            break