def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the device."""
        attr: dict[str, Any] = {}
        if isinstance(self.wemo, Maker):
            # Is the maker sensor on or off.
            if self.wemo.has_sensor:
                # Note a state of 1 matches the WeMo app 'not triggered'!
                if self.wemo.sensor_state:
                    attr[ATTR_SENSOR_STATE] = STATE_OFF
                else:
                    attr[ATTR_SENSOR_STATE] = STATE_ON

            # Is the maker switch configured as toggle(0) or momentary (1).
            if self.wemo.switch_mode:
                attr[ATTR_SWITCH_MODE] = MAKER_SWITCH_MOMENTARY
            else:
                attr[ATTR_SWITCH_MODE] = MAKER_SWITCH_TOGGLE

        if isinstance(self.wemo, (Insight, CoffeeMaker)):
            attr[ATTR_CURRENT_STATE_DETAIL] = self.detail_state

        if isinstance(self.wemo, Insight):
            attr[ATTR_ON_LATEST_TIME] = self.as_uptime(self.wemo.on_for)
            attr[ATTR_ON_TODAY_TIME] = self.as_uptime(self.wemo.today_on_time)
            attr[ATTR_ON_TOTAL_TIME] = self.as_uptime(self.wemo.total_on_time)
            attr[ATTR_POWER_THRESHOLD] = self.wemo.threshold_power_watts

        if isinstance(self.wemo, CoffeeMaker):
            attr[ATTR_COFFEMAKER_MODE] = self.wemo.mode

        return attr