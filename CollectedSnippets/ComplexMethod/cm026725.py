async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        transition = normalize_hue_transition(kwargs.get(ATTR_TRANSITION))
        xy_color = kwargs.get(ATTR_XY_COLOR)
        color_temp = normalize_hue_colortemp(
            kwargs.get(ATTR_COLOR_TEMP_KELVIN),
            self.min_color_temp_mireds,
            self.max_color_temp_mireds,
        )
        brightness = normalize_hue_brightness(kwargs.get(ATTR_BRIGHTNESS))
        if self._last_brightness and brightness is None:
            # The Hue bridge sets the brightness to 1% when turning on a bulb
            # when a transition was used to turn off the bulb.
            # This issue has been reported on the Hue forum several times:
            # https://developers.meethue.com/forum/t/brightness-turns-down-to-1-automatically-shortly-after-sending-off-signal-hue-bug/5692
            # https://developers.meethue.com/forum/t/lights-turn-on-with-lowest-brightness-via-siri-if-turned-off-via-api/6700
            # https://developers.meethue.com/forum/t/using-transitiontime-with-on-false-resets-bri-to-1/4585
            # https://developers.meethue.com/forum/t/bri-value-changing-in-switching-lights-on-off/6323
            # https://developers.meethue.com/forum/t/fade-in-fade-out/6673
            brightness = self._last_brightness
            self._last_brightness = None
        self._color_temp_active = color_temp is not None
        flash = kwargs.get(ATTR_FLASH)
        effect = effect_str = kwargs.get(ATTR_EFFECT)
        if effect_str == DEPRECATED_EFFECT_NONE:
            # deprecated effect "None" is now "off"
            effect_str = EFFECT_OFF
            async_create_issue(
                self.hass,
                DOMAIN,
                "deprecated_effect_none",
                breaks_in_ha_version="2025.10.0",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="deprecated_effect_none",
            )
            self.logger.warning(
                "Detected deprecated effect 'None' in %s, use 'off' instead. "
                "This will stop working in HA 2025.10",
                self.entity_id,
            )
        if effect_str == EFFECT_OFF:
            # ignore effect if set to "off" and we have no effect active
            # the special effect "off" is only used to stop an active effect
            # but sending it while no effect is active can actually result in issues
            # https://github.com/home-assistant/core/issues/122165
            effect = None if self.effect == EFFECT_OFF else EffectStatus.NO_EFFECT
        elif effect_str is not None:
            # work out if we got a regular effect or timed effect
            effect = EffectStatus(effect_str)
            if effect == EffectStatus.UNKNOWN:
                effect = TimedEffectStatus(effect_str)
                if transition is None:
                    # a transition is required for timed effect, default to 10 minutes
                    transition = 600000
            # we need to clear color values if an effect is applied
            color_temp = None
            xy_color = None

        if flash is not None:
            await self.async_set_flash(flash)
            # flash cannot be sent with other commands at the same time or result will be flaky
            # Hue's default behavior is that a light returns to its previous state for short
            # flash (identify) and the light is kept turned on for long flash (breathe effect)
            # Why is this flash alert/effect hidden in the turn_on/off commands ?
            return

        await self.bridge.async_request_call(
            self.controller.set_state,
            id=self.resource.id,
            on=True,
            brightness=brightness,
            color_xy=xy_color,
            color_temp=color_temp,
            transition_time=transition,
            effect=effect,
        )