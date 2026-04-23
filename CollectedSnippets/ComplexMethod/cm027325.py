async def async_discovery_update(
        self,
        discovery_payload: MQTTDiscoveryPayload,
    ) -> None:
        """Handle discovery update."""
        discovery_hash = get_discovery_hash(self._discovery_data)
        # Start discovery migration or rollback if migrate_discovery flag is set
        # and the discovery topic is valid and not yet migrating
        if (
            discovery_payload.migrate_discovery
            and self._migrate_discovery is None
            and self._discovery_data[ATTR_DISCOVERY_TOPIC]
            == discovery_payload.discovery_data[ATTR_DISCOVERY_TOPIC]
        ):
            self._migrate_discovery = self._discovery_data[ATTR_DISCOVERY_TOPIC]
            discovery_hash = self._discovery_data[ATTR_DISCOVERY_HASH]
            origin_info = get_origin_log_string(
                self._discovery_data[ATTR_DISCOVERY_PAYLOAD], include_url=False
            )
            action = "Rollback" if discovery_payload.device_discovery else "Migration"
            schema_type = "platform" if discovery_payload.device_discovery else "device"
            _LOGGER.info(
                "%s to MQTT %s discovery schema started for %s '%s'"
                "%s on topic %s. To complete %s, publish a %s discovery "
                "message with %s '%s'. After completed %s, "
                "publish an empty (retained) payload to %s",
                action,
                schema_type,
                discovery_hash[0],
                discovery_hash[1],
                origin_info,
                self._migrate_discovery,
                action.lower(),
                schema_type,
                discovery_hash[0],
                discovery_hash[1],
                action.lower(),
                self._migrate_discovery,
            )

            # Cleanup platform resources
            await self.async_tear_down()
            # Unregister and clean discovery
            stop_discovery_updates(
                self.hass, self._discovery_data, self._remove_discovery_updated
            )
            send_discovery_done(self.hass, self._discovery_data)
            return

        _LOGGER.debug(
            "Got update for %s with hash: %s '%s'",
            self.log_name,
            discovery_hash,
            discovery_payload,
        )
        new_discovery_topic = discovery_payload.discovery_data[ATTR_DISCOVERY_TOPIC]

        # Abort early if an update is not received via the registered discovery topic.
        # This can happen if a device and single component discovery payload
        # share the same discovery ID.
        if self._discovery_data[ATTR_DISCOVERY_TOPIC] != new_discovery_topic:
            # Prevent illegal updates
            old_origin_info = get_origin_log_string(
                self._discovery_data[ATTR_DISCOVERY_PAYLOAD], include_url=False
            )
            new_origin_info = get_origin_log_string(
                discovery_payload.discovery_data[ATTR_DISCOVERY_PAYLOAD],
                include_url=False,
            )
            new_origin_support_url = get_origin_support_url(
                discovery_payload.discovery_data[ATTR_DISCOVERY_PAYLOAD]
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
                "Received a conflicting MQTT discovery message for %s '%s' which was "
                "previously discovered on topic %s%s; the conflicting discovery "
                "message was received on topic %s%s; %s",
                discovery_hash[0],
                discovery_hash[1],
                self._discovery_data[ATTR_DISCOVERY_TOPIC],
                old_origin_info,
                new_discovery_topic,
                new_origin_info,
                get_support,
            )
            send_discovery_done(self.hass, self._discovery_data)
            return

        if (
            discovery_payload
            and discovery_payload != self._discovery_data[ATTR_DISCOVERY_PAYLOAD]
        ):
            _LOGGER.debug(
                "Updating %s with hash %s",
                self.log_name,
                discovery_hash,
            )
            try:
                await self.async_update(discovery_payload)
            finally:
                send_discovery_done(self.hass, self._discovery_data)
            self._discovery_data[ATTR_DISCOVERY_PAYLOAD] = discovery_payload
        elif not discovery_payload:
            # Unregister and clean up the current discovery instance
            stop_discovery_updates(
                self.hass, self._discovery_data, self._remove_discovery_updated
            )
            await self._async_tear_down()
            send_discovery_done(self.hass, self._discovery_data)
            _LOGGER.debug(
                "%s %s has been removed",
                self.log_name,
                discovery_hash,
            )
        else:
            # Normal update without change
            send_discovery_done(self.hass, self._discovery_data)
            _LOGGER.debug(
                "%s %s no changes",
                self.log_name,
                discovery_hash,
            )
            return