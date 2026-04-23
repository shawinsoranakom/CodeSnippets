def climate_google_modes(self):
        """Return supported Google modes."""
        modes = []
        attrs = self.state.attributes

        for mode in attrs.get(climate.ATTR_HVAC_MODES) or []:
            google_mode = self.hvac_to_google.get(mode)
            if google_mode and google_mode not in modes:
                modes.append(google_mode)

        for preset in attrs.get(climate.ATTR_PRESET_MODES) or []:
            google_mode = self.preset_to_google.get(preset)
            if google_mode and google_mode not in modes:
                modes.append(google_mode)

        return modes