def query_attributes(self) -> dict[str, Any]:
        """Return current modes."""
        attrs = self.state.attributes
        response: dict[str, Any] = {}
        mode_settings = {}

        if self.state.domain == fan.DOMAIN:
            if fan.ATTR_PRESET_MODES in attrs:
                mode_settings["preset mode"] = attrs.get(fan.ATTR_PRESET_MODE)
        elif self.state.domain == media_player.DOMAIN:
            if media_player.ATTR_SOUND_MODE_LIST in attrs:
                mode_settings["sound mode"] = attrs.get(media_player.ATTR_SOUND_MODE)
        elif self.state.domain in (input_select.DOMAIN, select.DOMAIN):
            mode_settings["option"] = self.state.state
        elif self.state.domain == humidifier.DOMAIN:
            if ATTR_MODE in attrs:
                mode_settings["mode"] = attrs.get(ATTR_MODE)
        elif self.state.domain == water_heater.DOMAIN:
            if water_heater.ATTR_OPERATION_MODE in attrs:
                mode_settings["operation mode"] = attrs.get(
                    water_heater.ATTR_OPERATION_MODE
                )
        elif self.state.domain == light.DOMAIN and (
            effect := attrs.get(light.ATTR_EFFECT)
        ):
            mode_settings["effect"] = effect

        if mode_settings:
            response["on"] = self.state.state not in (STATE_OFF, STATE_UNKNOWN)
            response["currentModeSettings"] = mode_settings

        return response