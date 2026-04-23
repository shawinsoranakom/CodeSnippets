async def async_instances_to_clients_raw(instances: list[dict[str, Any]]) -> None:
        """Convert instances to Hyperion clients."""
        device_registry = dr.async_get(hass)
        running_instances: set[int] = set()
        stopped_instances: set[int] = set()
        existing_instances = entry.runtime_data.instance_clients
        server_id = cast(str, entry.unique_id)

        # In practice, an instance can be in 3 states as seen by this function:
        #
        #    * Exists, and is running: Should be present in HASS/registry.
        #    * Exists, but is not running: Cannot add it yet, but entity may have be
        #      registered from a previous time it was running.
        #    * No longer exists at all: Should not be present in HASS/registry.

        # Add instances that are missing.
        for instance in instances:
            instance_num = instance.get(hyperion_const.KEY_INSTANCE)
            if instance_num is None:
                continue
            if not instance.get(hyperion_const.KEY_RUNNING, False):
                stopped_instances.add(instance_num)
                continue
            running_instances.add(instance_num)
            if instance_num in existing_instances:
                continue
            hyperion_client = await async_create_connect_hyperion_client(
                host, port, instance=instance_num, token=token
            )
            if not hyperion_client:
                continue
            existing_instances[instance_num] = hyperion_client
            instance_name = instance.get(hyperion_const.KEY_FRIENDLY_NAME, DEFAULT_NAME)
            async_dispatcher_send(
                hass,
                SIGNAL_INSTANCE_ADD.format(entry.entry_id),
                instance_num,
                instance_name,
            )

        # Remove entities that are not running instances on Hyperion.
        for instance_num in set(existing_instances) - running_instances:
            del existing_instances[instance_num]
            async_dispatcher_send(
                hass, SIGNAL_INSTANCE_REMOVE.format(entry.entry_id), instance_num
            )

        # Ensure every device associated with this config entry is still in the list of
        # motionEye cameras, otherwise remove the device (and thus entities).
        known_devices = {
            get_hyperion_device_id(server_id, instance_num)
            for instance_num in running_instances | stopped_instances
        }
        for device_entry in dr.async_entries_for_config_entry(
            device_registry, entry.entry_id
        ):
            for kind, key in device_entry.identifiers:
                if kind == DOMAIN and key in known_devices:
                    break
            else:
                device_registry.async_remove_device(device_entry.id)