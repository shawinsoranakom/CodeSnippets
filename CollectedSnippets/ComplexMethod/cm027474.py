async def async_setup_entry(hass: HomeAssistant, entry: HyperionConfigEntry) -> bool:
    """Set up Hyperion from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    token = entry.data.get(CONF_TOKEN)

    hyperion_client = await async_create_connect_hyperion_client(
        host, port, token=token, raw_connection=True
    )

    # Client won't connect? => Not ready.
    if not hyperion_client:
        raise ConfigEntryNotReady
    version = await hyperion_client.async_sysinfo_version()
    if version is not None:
        with suppress(ValueError):
            if AwesomeVersion(version) < AwesomeVersion(HYPERION_VERSION_WARN_CUTOFF):
                _LOGGER.warning(
                    (
                        "Using a Hyperion server version < %s is not recommended --"
                        " some features may be unavailable or may not function"
                        " correctly. Please consider upgrading: %s"
                    ),
                    HYPERION_VERSION_WARN_CUTOFF,
                    HYPERION_RELEASES_URL,
                )

    # Client needs authentication, but no token provided? => Reauth.
    auth_resp = await hyperion_client.async_is_auth_required()
    if (
        auth_resp is not None
        and client.ResponseOK(auth_resp)
        and auth_resp.get(hyperion_const.KEY_INFO, {}).get(
            hyperion_const.KEY_REQUIRED, False
        )
        and token is None
    ):
        await hyperion_client.async_client_disconnect()
        raise ConfigEntryAuthFailed

    # Client login doesn't work? => Reauth.
    if not await hyperion_client.async_client_login():
        await hyperion_client.async_client_disconnect()
        raise ConfigEntryAuthFailed

    # Cannot switch instance or cannot load state? => Not ready.
    if (
        not await hyperion_client.async_client_switch_instance()
        or not client.ServerInfoResponseOK(await hyperion_client.async_get_serverinfo())
    ):
        await hyperion_client.async_client_disconnect()
        raise ConfigEntryNotReady

    # We need 1 root client (to manage instances being removed/added) and then 1 client
    # per Hyperion server instance which is shared for all entities associated with
    # that instance.
    entry.runtime_data = HyperionData(
        root_client=hyperion_client,
        instance_clients={},
    )

    async def async_instances_to_clients(response: dict[str, Any]) -> None:
        """Convert instances to Hyperion clients."""
        if not response or hyperion_const.KEY_DATA not in response:
            return
        await async_instances_to_clients_raw(response[hyperion_const.KEY_DATA])

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

    hyperion_client.set_callbacks(
        {
            f"{hyperion_const.KEY_INSTANCE}-{hyperion_const.KEY_UPDATE}": async_instances_to_clients,
        }
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    assert hyperion_client
    if hyperion_client.instances is not None:
        await async_instances_to_clients_raw(hyperion_client.instances)

    return True