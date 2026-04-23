def parse_data(self, data, raw_data):
        """Parse data sent by gateway.

        Polling (proto v1, firmware version 1.4.1_159.0143)

        >> { "cmd":"read","sid":"158..."}
        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
            'cmd': 'read_ack', 'data': '{"voltage":3005}'}

        Multicast messages (proto v1, firmware version 1.4.1_159.0143)

        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
            'cmd': 'report', 'data': '{"status":"motion"}'}
        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
            'cmd': 'report', 'data': '{"no_motion":"120"}'}
        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
            'cmd': 'report', 'data': '{"no_motion":"180"}'}
        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
           'cmd': 'report', 'data': '{"no_motion":"300"}'}
        << {'model': 'motion', 'sid': '158...', 'short_id': 26331,
            'cmd': 'heartbeat', 'data': '{"voltage":3005}'}

        """
        if raw_data["cmd"] == "heartbeat":
            _LOGGER.debug(
                "Skipping heartbeat of the motion sensor. "
                "It can introduce an incorrect state because of a firmware "
                "bug (https://github.com/home-assistant/core/pull/"
                "11631#issuecomment-357507744)"
            )
            return None

        if NO_MOTION in data:
            self._no_motion_since = data[NO_MOTION]
            self._attr_is_on = False
            return True

        value = data.get(self._data_key)
        if value is None:
            return False

        if value == MOTION:
            if self._data_key == "motion_status":
                if self._unsub_set_no_motion:
                    self._unsub_set_no_motion()
                self._unsub_set_no_motion = async_call_later(
                    self._hass, 120, self._async_set_no_motion
                )

            if self.entity_id is not None:
                self._hass.bus.async_fire(
                    "xiaomi_aqara.motion", {"entity_id": self.entity_id}
                )

            self._no_motion_since = 0
            if self._attr_is_on:
                return False
            self._attr_is_on = True
            return True

        return False