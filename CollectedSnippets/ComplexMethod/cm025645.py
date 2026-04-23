def handle_event(self, event: dict) -> None:
        """Handle webhook events."""
        data = event["data"]

        if self.home.entity_id != data["home_id"]:
            return

        if data["event_type"] == EVENT_TYPE_SCHEDULE:
            # handle schedule change
            if "schedule_id" in data:
                selected_schedule = self.hass.data[DOMAIN][DATA_SCHEDULES][
                    self.home.entity_id
                ].get(data["schedule_id"])
                self._selected_schedule = getattr(
                    selected_schedule,
                    "name",
                    None,
                )
                self._attr_extra_state_attributes[ATTR_SELECTED_SCHEDULE] = (
                    self._selected_schedule
                )

                self._attr_extra_state_attributes[ATTR_SELECTED_SCHEDULE_ID] = getattr(
                    selected_schedule, "entity_id", None
                )

                self.async_write_ha_state()
                self.data_handler.async_force_update(self._signal_name)
            # ignore other schedule events
            return

        home = data["home"]

        if self.home.entity_id != home["id"]:
            return

        if data["event_type"] == EVENT_TYPE_THERM_MODE:
            self._attr_preset_mode = NETATMO_MAP_PRESET[home[EVENT_TYPE_THERM_MODE]]
            self._attr_hvac_mode = HVAC_MAP_NETATMO[self._attr_preset_mode]
            if self._attr_preset_mode == PRESET_FROST_GUARD:
                self._attr_target_temperature = self._hg_temperature
            elif self._attr_preset_mode == PRESET_AWAY:
                self._attr_target_temperature = self._away_temperature
            elif self._attr_preset_mode in [PRESET_SCHEDULE, PRESET_HOME]:
                self.async_update_callback()
                self.data_handler.async_force_update(self._signal_name)
            self.async_write_ha_state()
            return

        for room in home.get("rooms", []):
            if (
                data["event_type"] == EVENT_TYPE_SET_POINT
                and self.device.entity_id == room["id"]
            ):
                if room["therm_setpoint_mode"] == STATE_NETATMO_OFF:
                    self._attr_hvac_mode = HVACMode.OFF
                    self._attr_preset_mode = STATE_NETATMO_OFF
                    self._attr_target_temperature = 0
                elif room["therm_setpoint_mode"] == STATE_NETATMO_MAX:
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_preset_mode = PRESET_MAP_NETATMO[PRESET_BOOST]
                    self._attr_target_temperature = DEFAULT_MAX_TEMP
                elif room["therm_setpoint_mode"] == STATE_NETATMO_MANUAL:
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_target_temperature = room["therm_setpoint_temperature"]
                else:
                    self._attr_target_temperature = room["therm_setpoint_temperature"]
                    if self._attr_target_temperature == DEFAULT_MAX_TEMP:
                        self._attr_hvac_mode = HVACMode.HEAT
                self.async_write_ha_state()
                return

            if (
                data["event_type"] == EVENT_TYPE_CANCEL_SET_POINT
                and self.device.entity_id == room["id"]
            ):
                if self._attr_hvac_mode == HVACMode.OFF:
                    self._attr_hvac_mode = HVACMode.AUTO
                    self._attr_preset_mode = PRESET_MAP_NETATMO[PRESET_SCHEDULE]

                self.async_update_callback()
                self.async_write_ha_state()
                return