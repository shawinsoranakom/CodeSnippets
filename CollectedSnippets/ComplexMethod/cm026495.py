def capability_resources(self) -> dict[str, list[dict[str, Any]]]:
        """Return capabilityResources object."""

        # Fan Speed Percentage Resources
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_PERCENTAGE}":
            percentage_step = self.entity.attributes.get(fan.ATTR_PERCENTAGE_STEP)
            self._resource = AlexaPresetResource(
                labels=["Percentage", AlexaGlobalCatalog.SETTING_FAN_SPEED],
                min_value=0,
                max_value=100,
                # precision must be a divider of 100 and must be an integer; set step
                # size to 1 for a consistent behavior except for on/off fans
                precision=1 if percentage_step else 100,
                unit=AlexaGlobalCatalog.UNIT_PERCENT,
            )
            return self._resource.serialize_capability_resources()

        # Humidifier Target Humidity Resources
        if self.instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_HUMIDITY}":
            self._resource = AlexaPresetResource(
                labels=["Humidity", "Percentage", "Target humidity"],
                min_value=self.entity.attributes.get(humidifier.ATTR_MIN_HUMIDITY, 10),
                max_value=self.entity.attributes.get(humidifier.ATTR_MAX_HUMIDITY, 90),
                precision=1,
                unit=AlexaGlobalCatalog.UNIT_PERCENT,
            )
            return self._resource.serialize_capability_resources()

        # Cover Position Resources
        if self.instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
            self._resource = AlexaPresetResource(
                ["Position", AlexaGlobalCatalog.SETTING_OPENING],
                min_value=0,
                max_value=100,
                precision=1,
                unit=AlexaGlobalCatalog.UNIT_PERCENT,
            )
            return self._resource.serialize_capability_resources()

        # Cover Tilt Resources
        if self.instance == f"{cover.DOMAIN}.tilt":
            self._resource = AlexaPresetResource(
                ["Tilt", "Angle", AlexaGlobalCatalog.SETTING_DIRECTION],
                min_value=0,
                max_value=100,
                precision=1,
                unit=AlexaGlobalCatalog.UNIT_PERCENT,
            )
            return self._resource.serialize_capability_resources()

        # Input Number Value
        if self.instance == f"{input_number.DOMAIN}.{input_number.ATTR_VALUE}":
            min_value = float(self.entity.attributes[input_number.ATTR_MIN])
            max_value = float(self.entity.attributes[input_number.ATTR_MAX])
            precision = float(self.entity.attributes.get(input_number.ATTR_STEP, 1))
            unit = self.entity.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

            self._resource = AlexaPresetResource(
                ["Value", get_resource_by_unit_of_measurement(self.entity)],
                min_value=min_value,
                max_value=max_value,
                precision=precision,
                unit=unit,
            )
            self._resource.add_preset(
                value=min_value, labels=[AlexaGlobalCatalog.VALUE_MINIMUM]
            )
            self._resource.add_preset(
                value=max_value, labels=[AlexaGlobalCatalog.VALUE_MAXIMUM]
            )
            return self._resource.serialize_capability_resources()

        # Number Value
        if self.instance == f"{number.DOMAIN}.{number.ATTR_VALUE}":
            min_value = float(self.entity.attributes[number.ATTR_MIN])
            max_value = float(self.entity.attributes[number.ATTR_MAX])
            precision = float(self.entity.attributes.get(number.ATTR_STEP, 1))
            unit = self.entity.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

            self._resource = AlexaPresetResource(
                ["Value", get_resource_by_unit_of_measurement(self.entity)],
                min_value=min_value,
                max_value=max_value,
                precision=precision,
                unit=unit,
            )
            self._resource.add_preset(
                value=min_value, labels=[AlexaGlobalCatalog.VALUE_MINIMUM]
            )
            self._resource.add_preset(
                value=max_value, labels=[AlexaGlobalCatalog.VALUE_MAXIMUM]
            )
            return self._resource.serialize_capability_resources()

        # Vacuum Fan Speed Resources
        if self.instance == f"{vacuum.DOMAIN}.{vacuum.ATTR_FAN_SPEED}":
            speed_list = self.entity.attributes[vacuum.ATTR_FAN_SPEED_LIST]
            max_value = len(speed_list) - 1
            self._resource = AlexaPresetResource(
                labels=[AlexaGlobalCatalog.SETTING_FAN_SPEED],
                min_value=0,
                max_value=max_value,
                precision=1,
            )
            for index, speed in enumerate(speed_list):
                labels = [speed.replace("_", " ")]
                if index == 1:
                    labels.append(AlexaGlobalCatalog.VALUE_MINIMUM)
                if index == max_value:
                    labels.append(AlexaGlobalCatalog.VALUE_MAXIMUM)
                self._resource.add_preset(value=index, labels=labels)

            return self._resource.serialize_capability_resources()

        # Valve Position Resources
        if self.instance == f"{valve.DOMAIN}.{valve.ATTR_POSITION}":
            self._resource = AlexaPresetResource(
                ["Opening", AlexaGlobalCatalog.SETTING_OPENING],
                min_value=0,
                max_value=100,
                precision=1,
                unit=AlexaGlobalCatalog.UNIT_PERCENT,
            )
            return self._resource.serialize_capability_resources()

        return {}