async def execute(self, command, data, params, challenge):
        """Execute a SetModes command."""
        settings = params.get("updateModeSettings")

        if self.state.domain == fan.DOMAIN:
            preset_mode = settings["preset mode"]
            await self.hass.services.async_call(
                fan.DOMAIN,
                fan.SERVICE_SET_PRESET_MODE,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    fan.ATTR_PRESET_MODE: preset_mode,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == input_select.DOMAIN:
            option = settings["option"]
            await self.hass.services.async_call(
                input_select.DOMAIN,
                input_select.SERVICE_SELECT_OPTION,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    input_select.ATTR_OPTION: option,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == select.DOMAIN:
            option = settings["option"]
            await self.hass.services.async_call(
                select.DOMAIN,
                select.SERVICE_SELECT_OPTION,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    select.ATTR_OPTION: option,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == humidifier.DOMAIN:
            requested_mode = settings["mode"]
            await self.hass.services.async_call(
                humidifier.DOMAIN,
                humidifier.SERVICE_SET_MODE,
                {
                    ATTR_MODE: requested_mode,
                    ATTR_ENTITY_ID: self.state.entity_id,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == water_heater.DOMAIN:
            requested_mode = settings["operation mode"]
            await self.hass.services.async_call(
                water_heater.DOMAIN,
                water_heater.SERVICE_SET_OPERATION_MODE,
                {
                    water_heater.ATTR_OPERATION_MODE: requested_mode,
                    ATTR_ENTITY_ID: self.state.entity_id,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == light.DOMAIN:
            requested_effect = settings["effect"]
            await self.hass.services.async_call(
                light.DOMAIN,
                SERVICE_TURN_ON,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    light.ATTR_EFFECT: requested_effect,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )
            return

        if self.state.domain == media_player.DOMAIN and (
            sound_mode := settings.get("sound mode")
        ):
            await self.hass.services.async_call(
                media_player.DOMAIN,
                media_player.SERVICE_SELECT_SOUND_MODE,
                {
                    ATTR_ENTITY_ID: self.state.entity_id,
                    media_player.ATTR_SOUND_MODE: sound_mode,
                },
                blocking=not self.config.should_report_state,
                context=data.context,
            )

        _LOGGER.info(
            "Received an Options command for unrecognised domain %s",
            self.state.domain,
        )
        return