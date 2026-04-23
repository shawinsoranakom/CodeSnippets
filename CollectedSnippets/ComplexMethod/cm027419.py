def preset_mode(self) -> str | None:
        """Return current preset mode."""
        events = self.thermostat["events"]
        for event in events:
            if not event["running"]:
                continue

            if event["type"] == "hold":
                if event["holdClimateRef"] == "away" and is_indefinite_hold(
                    event["startDate"], event["endDate"]
                ):
                    return PRESET_AWAY_INDEFINITELY

                if name := self.comfort_settings.get(event["holdClimateRef"]):
                    return ECOBEE_TO_HASS_PRESET.get(name, name)

                # Any hold not based on a climate is a temp hold
                return PRESET_TEMPERATURE
            if event["type"].startswith("auto"):
                # All auto modes are treated as holds
                return event["type"][4:].lower()
            if event["type"] == "vacation":
                self.vacation = event["name"]
                return PRESET_VACATION

        if name := self.comfort_settings.get(
            self.thermostat["program"]["currentClimateRef"]
        ):
            return ECOBEE_TO_HASS_PRESET.get(name, name)

        return None