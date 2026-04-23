def get_property(self, name: str) -> Any:
        """Read and return a property."""
        if name != "rangeValue":
            raise UnsupportedProperty(name)

        # Return None for unavailable and unknown states.
        # Allows the Alexa.EndpointHealth Interface to handle the unavailable
        # state in a stateReport.
        if self.entity.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
            return None

        # Cover Position
        if self.instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
            return self.entity.attributes.get(cover.ATTR_CURRENT_POSITION)

        # Cover Tilt
        if self.instance == f"{cover.DOMAIN}.tilt":
            return self.entity.attributes.get(cover.ATTR_CURRENT_TILT_POSITION)

        # Fan speed percentage
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_PERCENTAGE}":
            supported = self.entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
            if supported and fan.FanEntityFeature.SET_SPEED:
                return self.entity.attributes.get(fan.ATTR_PERCENTAGE)
            return 100 if self.entity.state == fan.STATE_ON else 0

        # Humidifier target humidity
        if self.instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_HUMIDITY}":
            # If the humidifier is turned off the target humidity attribute is not set.
            # We return 0 to make clear we do not know the current value.
            return self.entity.attributes.get(humidifier.ATTR_HUMIDITY, 0)

        # Input Number Value
        if self.instance == f"{input_number.DOMAIN}.{input_number.ATTR_VALUE}":
            return float(self.entity.state)

        # Number Value
        if self.instance == f"{number.DOMAIN}.{number.ATTR_VALUE}":
            return float(self.entity.state)

        # Vacuum Fan Speed
        if self.instance == f"{vacuum.DOMAIN}.{vacuum.ATTR_FAN_SPEED}":
            speed_list = self.entity.attributes.get(vacuum.ATTR_FAN_SPEED_LIST)
            speed = self.entity.attributes.get(vacuum.ATTR_FAN_SPEED)
            if speed_list is not None and speed is not None:
                return next((i for i, v in enumerate(speed_list) if v == speed), None)

        # Valve Position
        if self.instance == f"{valve.DOMAIN}.{valve.ATTR_POSITION}":
            return self.entity.attributes.get(valve.ATTR_CURRENT_POSITION)

        return None