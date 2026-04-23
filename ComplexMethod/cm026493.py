def capability_resources(self) -> dict[str, list[dict[str, Any]]]:
        """Return capabilityResources object."""

        # Fan Direction Resource
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_DIRECTION}":
            self._resource = AlexaModeResource(
                [AlexaGlobalCatalog.SETTING_DIRECTION], False
            )
            self._resource.add_mode(
                f"{fan.ATTR_DIRECTION}.{fan.DIRECTION_FORWARD}", [fan.DIRECTION_FORWARD]
            )
            self._resource.add_mode(
                f"{fan.ATTR_DIRECTION}.{fan.DIRECTION_REVERSE}", [fan.DIRECTION_REVERSE]
            )
            return self._resource.serialize_capability_resources()

        # Fan preset_mode
        if self.instance == f"{fan.DOMAIN}.{fan.ATTR_PRESET_MODE}":
            self._resource = AlexaModeResource(
                [AlexaGlobalCatalog.SETTING_PRESET], False
            )
            preset_modes = self.entity.attributes.get(fan.ATTR_PRESET_MODES) or []
            for preset_mode in preset_modes:
                self._resource.add_mode(
                    f"{fan.ATTR_PRESET_MODE}.{preset_mode}", [preset_mode]
                )
            # Fans with a single preset_mode completely break Alexa discovery, add a
            # fake preset (see issue #53832).
            if len(preset_modes) == 1:
                self._resource.add_mode(
                    f"{fan.ATTR_PRESET_MODE}.{PRESET_MODE_NA}", [PRESET_MODE_NA]
                )
            return self._resource.serialize_capability_resources()

        # Humidifier modes
        if self.instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_MODE}":
            self._resource = AlexaModeResource([AlexaGlobalCatalog.SETTING_MODE], False)
            modes = self.entity.attributes.get(humidifier.ATTR_AVAILABLE_MODES) or []
            for mode in modes:
                self._resource.add_mode(f"{humidifier.ATTR_MODE}.{mode}", [mode])
            # Humidifiers or Fans with a single mode completely break Alexa discovery,
            # add a fake preset (see issue #53832).
            if len(modes) == 1:
                self._resource.add_mode(
                    f"{humidifier.ATTR_MODE}.{PRESET_MODE_NA}", [PRESET_MODE_NA]
                )
            return self._resource.serialize_capability_resources()

        # Water heater operation modes
        if self.instance == f"{water_heater.DOMAIN}.{water_heater.ATTR_OPERATION_MODE}":
            self._resource = AlexaModeResource([AlexaGlobalCatalog.SETTING_MODE], False)
            operation_modes = (
                self.entity.attributes.get(water_heater.ATTR_OPERATION_LIST) or []
            )
            for operation_mode in operation_modes:
                self._resource.add_mode(
                    f"{water_heater.ATTR_OPERATION_MODE}.{operation_mode}",
                    [operation_mode],
                )
            # Devices with a single mode completely break Alexa discovery,
            # add a fake preset (see issue #53832).
            if len(operation_modes) == 1:
                self._resource.add_mode(
                    f"{water_heater.ATTR_OPERATION_MODE}.{PRESET_MODE_NA}",
                    [PRESET_MODE_NA],
                )
            return self._resource.serialize_capability_resources()

        # Remote Resource
        if self.instance == f"{remote.DOMAIN}.{remote.ATTR_ACTIVITY}":
            # Use the mode controller for a remote because the input controller
            # only allows a preset of names as an input.
            self._resource = AlexaModeResource([AlexaGlobalCatalog.SETTING_MODE], False)
            activities = self.entity.attributes.get(remote.ATTR_ACTIVITY_LIST) or []
            for activity in activities:
                self._resource.add_mode(
                    f"{remote.ATTR_ACTIVITY}.{activity}", [activity]
                )
            # Remotes with a single activity completely break Alexa discovery, add a
            # fake activity to the mode controller (see issue #53832).
            if len(activities) == 1:
                self._resource.add_mode(
                    f"{remote.ATTR_ACTIVITY}.{PRESET_MODE_NA}", [PRESET_MODE_NA]
                )
            return self._resource.serialize_capability_resources()

        # Cover Position Resources
        if self.instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
            self._resource = AlexaModeResource(
                ["Position", AlexaGlobalCatalog.SETTING_OPENING], False
            )
            self._resource.add_mode(
                f"{cover.ATTR_POSITION}.{cover.CoverState.OPEN}",
                [AlexaGlobalCatalog.VALUE_OPEN],
            )
            self._resource.add_mode(
                f"{cover.ATTR_POSITION}.{cover.CoverState.CLOSED}",
                [AlexaGlobalCatalog.VALUE_CLOSE],
            )
            self._resource.add_mode(
                f"{cover.ATTR_POSITION}.custom",
                ["Custom", AlexaGlobalCatalog.SETTING_PRESET],
            )
            return self._resource.serialize_capability_resources()

        # Valve position resources
        if self.instance == f"{valve.DOMAIN}.state":
            supported_features = self.entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
            self._resource = AlexaModeResource(
                ["Preset", AlexaGlobalCatalog.SETTING_PRESET], False
            )
            modes = 0
            if supported_features & valve.ValveEntityFeature.OPEN:
                self._resource.add_mode(
                    f"state.{valve.STATE_OPEN}",
                    ["Open", AlexaGlobalCatalog.SETTING_PRESET],
                )
                modes += 1
            if supported_features & valve.ValveEntityFeature.CLOSE:
                self._resource.add_mode(
                    f"state.{valve.STATE_CLOSED}",
                    ["Closed", AlexaGlobalCatalog.SETTING_PRESET],
                )
                modes += 1

            # Alexa requires at least 2 modes
            if modes == 1:
                self._resource.add_mode(f"state.{PRESET_MODE_NA}", [PRESET_MODE_NA])

            return self._resource.serialize_capability_resources()

        return {}