def _state_message_received(self, msg: ReceiveMessage) -> None:
        """Handle state MQTT message."""
        payload = json_loads_object(msg.payload)
        if STATE in payload and (
            (state := payload[STATE]) in POSSIBLE_STATES or state is None
        ):
            self._attr_activity = (
                POSSIBLE_STATES[cast(str, state)] if payload[STATE] else None
            )
            del payload[STATE]
        if (
            (segments_payload := payload.pop(SEGMENTS, None))
            and self._clean_segments_command_topic is not None
            and isinstance(segments_payload, dict)
            and (
                segments := [
                    Segment(id=segment_id, name=str(segment_name))
                    for segment_id, segment_name in segments_payload.items()
                ]
            )
        ):
            self._segments = segments
            self._attr_supported_features |= VacuumEntityFeature.CLEAN_AREA
            if (last_seen := self.last_seen_segments) is not None and {
                s.id: s for s in last_seen
            } != {s.id: s for s in self._segments}:
                self.async_create_segments_issue()

        self._update_state_attributes(payload)