def async_discovery_message_received(msg: ReceiveMessage) -> None:
        """Process the received message."""
        mqtt_data.last_discovery = msg.timestamp
        payload = msg.payload
        topic = msg.topic
        topic_trimmed = topic.replace(f"{discovery_topic}/", "", 1)

        if not (match := TOPIC_MATCHER.match(topic_trimmed)):
            if topic_trimmed.endswith("config"):
                _LOGGER.warning(
                    (
                        "Received message on illegal discovery topic '%s'. The topic"
                        " contains non allowed characters. For more information see "
                        "https://www.home-assistant.io/integrations/mqtt/#discovery-topic"
                    ),
                    topic,
                )
            return

        component, node_id, object_id = match.groups()

        discovered_components: list[MqttComponentConfig] = []
        if component == CONF_DEVICE:
            # Process device based discovery message and regenerate
            # cleanup config for the all the components that are being removed.
            # This is done when a component in the device config is omitted and detected
            # as being removed, or when the device config update payload is empty.
            # In that case this will regenerate a cleanup message for all every already
            # discovered components that were linked to the initial device discovery.
            device_discovery_payload = _parse_device_payload(
                hass, payload, object_id, node_id
            )
            if not device_discovery_payload:
                return
            device_config: dict[str, Any]
            origin_config: dict[str, Any] | None
            component_configs: dict[str, dict[str, Any]]
            device_config = device_discovery_payload[CONF_DEVICE]
            origin_config = device_discovery_payload.get(CONF_ORIGIN)
            component_configs = device_discovery_payload[CONF_COMPONENTS]
            for component_id, config in component_configs.items():
                component = config.pop(CONF_PLATFORM)
                # The object_id in the device discovery topic is the unique identifier.
                # It is used as node_id for the components it contains.
                component_node_id = object_id
                # The component_id in the discovery playload is used as object_id
                # If we have an additional node_id in the discovery topic,
                # we extend the component_id with it.
                component_object_id = (
                    f"{node_id} {component_id}" if node_id else component_id
                )
                # We add wrapper to the discovery payload with the discovery data.
                # If the dict is empty after removing the platform, the payload is
                # assumed to remove the existing config and we do not want to add
                # device or orig or shared availability attributes.
                if discovery_payload := MQTTDiscoveryPayload(config):
                    discovery_payload[CONF_DEVICE] = device_config
                    discovery_payload[CONF_ORIGIN] = origin_config
                    # Only assign shared config options
                    # when they are not set at entity level
                    _merge_common_device_options(
                        discovery_payload, device_discovery_payload
                    )
                discovery_payload.device_discovery = True
                discovery_payload.migrate_discovery = (
                    device_discovery_payload.migrate_discovery
                )
                discovered_components.append(
                    MqttComponentConfig(
                        component,
                        component_object_id,
                        component_node_id,
                        discovery_payload,
                    )
                )
            _LOGGER.debug(
                "Process device discovery payload %s", device_discovery_payload
            )
            device_discovery_id = f"{node_id} {object_id}" if node_id else object_id
            message = f"Processing device discovery for '{device_discovery_id}'"
            async_log_discovery_origin_info(
                message, MQTTDiscoveryPayload(device_discovery_payload)
            )

        else:
            # Process component based discovery message
            try:
                discovery_payload = MQTTDiscoveryPayload(
                    json_loads_object(payload) if payload else {}
                )
            except ValueError:
                _LOGGER.warning("Unable to parse JSON %s: '%s'", object_id, payload)
                return
            if not _async_process_discovery_migration(discovery_payload):
                _replace_all_abbreviations(discovery_payload)
                if not _valid_origin_info(discovery_payload):
                    return
            discovered_components.append(
                MqttComponentConfig(component, object_id, node_id, discovery_payload)
            )

        discovery_pending_discovered = mqtt_data.discovery_pending_discovered
        for component_config in discovered_components:
            component = component_config.component
            node_id = component_config.node_id
            object_id = component_config.object_id
            discovery_payload = component_config.discovery_payload

            if TOPIC_BASE in discovery_payload:
                _replace_topic_base(discovery_payload)

            # If present, the node_id will be included in the discovery_id.
            discovery_id = f"{node_id} {object_id}" if node_id else object_id
            discovery_hash = (component, discovery_id)

            # Attach MQTT topic to the payload, used for debug prints
            discovery_payload.discovery_data = {
                ATTR_DISCOVERY_HASH: discovery_hash,
                ATTR_DISCOVERY_PAYLOAD: discovery_payload,
                ATTR_DISCOVERY_TOPIC: topic,
            }

            if discovery_hash in discovery_pending_discovered:
                pending = discovery_pending_discovered[discovery_hash]["pending"]
                pending.appendleft(discovery_payload)
                _LOGGER.debug(
                    "Component has already been discovered: %s %s, queuing update",
                    component,
                    discovery_id,
                )
                return

            async_process_discovery_payload(component, discovery_id, discovery_payload)