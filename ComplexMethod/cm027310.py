def _event_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        if msg.retain:
            _LOGGER.debug(
                "Ignoring event trigger from replayed retained payload '%s' on topic %s",
                msg.payload,
                msg.topic,
            )
            return
        event_attributes: dict[str, Any] = {}
        event_type: str
        try:
            payload = self._template(msg.payload, PayloadSentinel.DEFAULT)
        except MqttValueTemplateException as exc:
            _LOGGER.warning(exc)
            return
        if (
            not payload
            or payload is PayloadSentinel.DEFAULT
            or payload in (PAYLOAD_NONE, PAYLOAD_EMPTY_JSON)
        ):
            _LOGGER.debug(
                "Ignoring empty payload '%s' after rendering for topic %s",
                payload,
                msg.topic,
            )
            return
        try:
            event_attributes = json_loads_object(payload)
            event_type = str(event_attributes.pop(event.ATTR_EVENT_TYPE))
            _LOGGER.debug(
                (
                    "JSON event data detected after processing payload '%s' on"
                    " topic %s, type %s, attributes %s"
                ),
                payload,
                msg.topic,
                event_type,
                event_attributes,
            )
        except KeyError:
            _LOGGER.warning(
                "`event_type` missing in JSON event payload, '%s' on topic %s",
                payload,
                msg.topic,
            )
            return
        except JSON_DECODE_EXCEPTIONS:
            _LOGGER.warning(
                (
                    "No valid JSON event payload detected, "
                    "value after processing payload"
                    " '%s' on topic %s"
                ),
                payload,
                msg.topic,
            )
            return
        try:
            self._trigger_event(event_type, event_attributes)
        except ValueError:
            _LOGGER.warning(
                "Invalid event type %s for %s received on topic %s, payload %s",
                event_type,
                self.entity_id,
                msg.topic,
                payload,
            )
            return
        mqtt_data = self.hass.data[DATA_MQTT]
        mqtt_data.state_write_requests.write_state_request(self)