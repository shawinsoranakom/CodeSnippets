def async_process_discovery_payload(
        component: str, discovery_id: str, payload: MQTTDiscoveryPayload
    ) -> None:
        """Process the payload of a new discovery."""

        _LOGGER.debug("Process component discovery payload %s", payload)
        discovery_hash = (component, discovery_id)

        already_discovered = discovery_hash in mqtt_data.discovery_already_discovered
        if (
            already_discovered or payload
        ) and discovery_hash not in mqtt_data.discovery_pending_discovered:
            discovery_pending_discovered = mqtt_data.discovery_pending_discovered

            @callback
            def discovery_done(_: Any) -> None:
                pending = discovery_pending_discovered[discovery_hash]["pending"]
                _LOGGER.debug("Pending discovery for %s: %s", discovery_hash, pending)
                if not pending:
                    discovery_pending_discovered[discovery_hash]["unsub"]()
                    discovery_pending_discovered.pop(discovery_hash)
                else:
                    payload = pending.pop()
                    async_process_discovery_payload(component, discovery_id, payload)

            discovery_pending_discovered[discovery_hash] = {
                "unsub": async_dispatcher_connect(
                    hass,
                    MQTT_DISCOVERY_DONE.format(*discovery_hash),
                    discovery_done,
                ),
                "pending": deque([]),
            }

        if component not in mqtt_data.platforms_loaded and payload:
            # Load component first
            config_entry.async_create_task(
                hass, _async_component_setup(component, payload)
            )
        elif already_discovered:
            # Dispatch update
            message = f"Component has already been discovered: {component} {discovery_id}, sending update"
            async_log_discovery_origin_info(message, payload)
            async_dispatcher_send(
                hass, MQTT_DISCOVERY_UPDATED.format(*discovery_hash), payload
            )
        elif payload:
            _async_add_component(payload)
        else:
            entity_registry = er.async_get(hass)
            if (
                (
                    entity_hash := mqtt_data.discovery_discovered_and_disabled.pop(
                        discovery_hash, None
                    )
                )
                and (entity_id := entity_registry.entities.get_entity_id(entity_hash))
                and (entity_entry := entity_registry.async_get(entity_id))
            ):
                # Cleanup discovered disabled entity / device
                entity_registry.async_remove(entity_id)
                hass.async_create_task(
                    async_cleanup_device_registry(
                        hass,
                        device_id=entity_entry.device_id,
                        config_entry_id=entity_entry.config_entry_id,
                    ),
                    name=f"Check for cleanup device registry for {entity_id}",
                )

            # Finish handling discovery message
            async_dispatcher_send(
                hass, MQTT_DISCOVERY_DONE.format(*discovery_hash), None
            )