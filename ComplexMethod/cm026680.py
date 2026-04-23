def _message_callback(self, message):
        """Handle received messages."""
        if message.alarm_sounding or message.fire_alarm:
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        elif message.armed_away:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif message.armed_home and (message.entry_delay_off or message.perimeter_only):
            self._attr_alarm_state = AlarmControlPanelState.ARMED_NIGHT
        elif message.armed_home:
            self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

        self._attr_extra_state_attributes = {
            "ac_power": message.ac_power,
            "alarm_event_occurred": message.alarm_event_occurred,
            "backlight_on": message.backlight_on,
            "battery_low": message.battery_low,
            "check_zone": message.check_zone,
            "chime": message.chime_on,
            "entry_delay_off": message.entry_delay_off,
            "programming_mode": message.programming_mode,
            "ready": message.ready,
            "zone_bypassed": message.zone_bypassed,
        }
        self.schedule_update_ha_state()