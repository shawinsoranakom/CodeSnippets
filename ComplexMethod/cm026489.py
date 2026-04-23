def get_property(self, name: str) -> Any:
        """Read and return a property."""
        if name != "powerState":
            raise UnsupportedProperty(name)

        if self.entity.domain == climate.DOMAIN:
            is_on = self.entity.state != climate.HVACMode.OFF
        elif self.entity.domain == fan.DOMAIN:
            is_on = self.entity.state == fan.STATE_ON
        elif self.entity.domain == humidifier.DOMAIN:
            is_on = self.entity.state == humidifier.STATE_ON
        elif self.entity.domain == remote.DOMAIN:
            is_on = self.entity.state not in (STATE_OFF, STATE_UNKNOWN)
        elif self.entity.domain == vacuum.DOMAIN:
            is_on = self.entity.state == vacuum.VacuumActivity.CLEANING
        elif self.entity.domain == timer.DOMAIN:
            is_on = self.entity.state != STATE_IDLE
        elif self.entity.domain == water_heater.DOMAIN:
            is_on = self.entity.state not in (STATE_OFF, STATE_UNKNOWN)
        else:
            is_on = self.entity.state != STATE_OFF

        return "ON" if is_on else "OFF"