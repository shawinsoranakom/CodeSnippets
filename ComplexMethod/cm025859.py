def __validate_color_mode(
        self,
        color_mode: ColorMode | None,
        supported_color_modes: set[ColorMode],
        effect: str | None,
    ) -> None:
        """Validate the color mode."""
        if color_mode is None or color_mode == ColorMode.UNKNOWN:
            # The light is turned off or in an unknown state
            return

        if not effect or effect == EFFECT_OFF:
            # No effect is active, the light must set color mode to one of the supported
            # color modes
            if color_mode in supported_color_modes:
                return
            raise HomeAssistantError(
                f"{self.entity_id} ({type(self)}) set to unsupported color mode "
                f"{color_mode}, expected one of {supported_color_modes}"
            )

        # When an effect is active, the color mode should indicate what adjustments are
        # supported by the effect. To make this possible, we allow the light to set its
        # color mode to on_off, and to brightness if the light allows adjusting
        # brightness, in addition to the otherwise supported color modes.
        effect_color_modes = supported_color_modes | {ColorMode.ONOFF}
        if brightness_supported(effect_color_modes):
            effect_color_modes.add(ColorMode.BRIGHTNESS)

        if color_mode in effect_color_modes:
            return

        raise HomeAssistantError(
            f"{self.entity_id} ({type(self)}) set to unsupported color mode "
            f"{color_mode} when rendering an effect, expected one "
            f"of {effect_color_modes}"
        )