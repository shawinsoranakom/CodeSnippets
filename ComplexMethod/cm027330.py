def _handle_state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle receiving state message via MQTT."""
        payload = self._templates[CONF_VALUE_TEMPLATE](
            msg.payload, PayloadSentinel.DEFAULT
        )

        if payload is PayloadSentinel.DEFAULT:
            _LOGGER.warning(
                "Unable to process payload '%s' for topic %s, with value template '%s'",
                msg.payload,
                msg.topic,
                self._config.get(CONF_VALUE_TEMPLATE),
            )
            return

        if not payload or payload == PAYLOAD_EMPTY_JSON:
            _LOGGER.debug(
                "Ignoring empty payload '%s' after rendering for topic %s",
                payload,
                msg.topic,
            )
            return

        json_payload: dict[str, Any] = {}
        try:
            rendered_json_payload = json_loads(payload)
            if isinstance(rendered_json_payload, dict):
                _LOGGER.debug(
                    "JSON payload detected after processing payload '%s' on topic %s",
                    rendered_json_payload,
                    msg.topic,
                )
                json_payload = MQTT_JSON_UPDATE_SCHEMA(rendered_json_payload)
            else:
                _LOGGER.debug(
                    (
                        "Non-dictionary JSON payload detected after processing"
                        " payload '%s' on topic %s"
                    ),
                    payload,
                    msg.topic,
                )
                json_payload = {"installed_version": str(payload)}
        except vol.MultipleInvalid as exc:
            _LOGGER.warning(
                (
                    "Schema violation after processing payload '%s'"
                    " on topic '%s' for entity '%s': %s"
                ),
                payload,
                msg.topic,
                self.entity_id,
                exc,
            )
            return
        except JSON_DECODE_EXCEPTIONS:
            _LOGGER.debug(
                (
                    "No valid (JSON) payload detected after processing payload '%s'"
                    " on topic '%s' for entity '%s'"
                ),
                payload,
                msg.topic,
                self.entity_id,
            )
            json_payload["installed_version"] = str(payload)

        if "installed_version" in json_payload:
            self._attr_installed_version = json_payload["installed_version"]

        if "latest_version" in json_payload:
            self._attr_latest_version = json_payload["latest_version"]

        if "title" in json_payload:
            self._attr_title = json_payload["title"]

        if "release_summary" in json_payload:
            self._attr_release_summary = json_payload["release_summary"]

        if "release_url" in json_payload:
            self._attr_release_url = json_payload["release_url"]

        if "entity_picture" in json_payload:
            self._attr_entity_picture = json_payload["entity_picture"]

        if "update_percentage" in json_payload:
            self._attr_update_percentage = json_payload["update_percentage"]
            self._attr_in_progress = self._attr_update_percentage is not None

        if "in_progress" in json_payload:
            self._attr_in_progress = json_payload["in_progress"]