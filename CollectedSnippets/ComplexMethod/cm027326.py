def _async_discovery_callback(self, payload: MQTTDiscoveryPayload) -> None:
        """Handle discovery update.

        If the payload has changed we will create a task to
        do the discovery update.

        As this callback can fire when nothing has changed, this
        is a normal function to avoid task creation until it is needed.
        """
        if TYPE_CHECKING:
            assert self._discovery_data
        discovery_hash = get_discovery_hash(self._discovery_data)
        # Start discovery migration or rollback if migrate_discovery flag is set
        # and the discovery topic is valid and not yet migrating
        if (
            payload.migrate_discovery
            and self._migrate_discovery is None
            and self._discovery_data[ATTR_DISCOVERY_TOPIC]
            == payload.discovery_data[ATTR_DISCOVERY_TOPIC]
        ):
            if self.unique_id is None or self.device_info is None:
                _LOGGER.error(
                    "Discovery migration is not possible for "
                    "for entity %s on topic %s. A unique_id "
                    "and device context is required, got unique_id: %s, device: %s",
                    self.entity_id,
                    self._discovery_data[ATTR_DISCOVERY_TOPIC],
                    self.unique_id,
                    self.device_info,
                )
                send_discovery_done(self.hass, self._discovery_data)
                return

            self._migrate_discovery = self._discovery_data[ATTR_DISCOVERY_TOPIC]
            discovery_hash = self._discovery_data[ATTR_DISCOVERY_HASH]
            origin_info = get_origin_log_string(
                self._discovery_data[ATTR_DISCOVERY_PAYLOAD], include_url=False
            )
            action = "Rollback" if payload.device_discovery else "Migration"
            schema_type = "platform" if payload.device_discovery else "device"
            _LOGGER.info(
                "%s to MQTT %s discovery schema started for entity %s"
                "%s on topic %s. To complete %s, publish a %s discovery "
                "message with %s entity '%s'. After completed %s, "
                "publish an empty (retained) payload to %s",
                action,
                schema_type,
                self.entity_id,
                origin_info,
                self._migrate_discovery,
                action.lower(),
                schema_type,
                discovery_hash[0],
                discovery_hash[1],
                action.lower(),
                self._migrate_discovery,
            )
        old_payload = self._discovery_data[ATTR_DISCOVERY_PAYLOAD]
        _LOGGER.debug(
            "Got update for entity with hash: %s '%s'",
            discovery_hash,
            payload,
        )
        new_discovery_topic = payload.discovery_data[ATTR_DISCOVERY_TOPIC]
        # Abort early if an update is not received via the registered discovery topic.
        # This can happen if a device and single component discovery payload
        # share the same discovery ID.
        if self._discovery_data[ATTR_DISCOVERY_TOPIC] != new_discovery_topic:
            # Prevent illegal updates
            old_origin_info = get_origin_log_string(
                self._discovery_data[ATTR_DISCOVERY_PAYLOAD], include_url=False
            )
            new_origin_info = get_origin_log_string(
                payload.discovery_data[ATTR_DISCOVERY_PAYLOAD], include_url=False
            )
            new_origin_support_url = get_origin_support_url(
                payload.discovery_data[ATTR_DISCOVERY_PAYLOAD]
            )
            if new_origin_support_url:
                get_support = f"for support visit {new_origin_support_url}"
            else:
                get_support = (
                    "for documentation on migration to device schema or rollback to "
                    "discovery schema, visit https://www.home-assistant.io/integrations/"
                    "mqtt/#migration-from-single-component-to-device-based-discovery"
                )
            _LOGGER.warning(
                "Received a conflicting MQTT discovery message for entity %s; the "
                "entity was previously discovered on topic %s%s; the conflicting "
                "discovery message was received on topic %s%s; %s",
                self.entity_id,
                self._discovery_data[ATTR_DISCOVERY_TOPIC],
                old_origin_info,
                new_discovery_topic,
                new_origin_info,
                get_support,
            )
            send_discovery_done(self.hass, self._discovery_data)
            return

        debug_info.update_entity_discovery_data(self.hass, payload, self.entity_id)
        if not payload:
            # Empty payload: Remove component
            if self._migrate_discovery is None:
                _LOGGER.info("Removing component: %s", self.entity_id)
            else:
                _LOGGER.info("Unloading component: %s", self.entity_id)
            self.hass.async_create_task(
                self._async_process_discovery_update_and_remove()
            )
        elif self._discovery_update:
            if old_payload != payload:
                # Non-empty, changed payload: Notify component
                _LOGGER.info("Updating component: %s", self.entity_id)
                self.hass.async_create_task(
                    self._async_process_discovery_update(
                        payload, self._discovery_update, self._discovery_data
                    )
                )
            else:
                # Non-empty, unchanged payload: Ignore to avoid changing states
                _LOGGER.debug("Ignoring unchanged update for: %s", self.entity_id)
                send_discovery_done(self.hass, self._discovery_data)