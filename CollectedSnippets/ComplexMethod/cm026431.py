def __init__(  # pylint: disable=super-init-not-called
        self, name: str, config: dict[str, Any]
    ) -> None:
        """Initialize the features."""

        # Setup state and brightness
        self.setup_state_template(
            "_attr_is_on", template_validators.boolean(self, CONF_STATE)
        )
        self.setup_template(
            CONF_LEVEL,
            "_attr_brightness",
            template_validators.number(self, CONF_LEVEL, 0, 255, int),
        )

        # Setup Color temperature
        self.setup_template(
            CONF_TEMPERATURE,
            "_attr_color_temp_kelvin",
            self._validate_temperature,
            self._update_color("_attr_color_temp_kelvin", ColorMode.COLOR_TEMP),
        )

        # Setup Hue Saturation
        self.setup_template(
            CONF_HS,
            "_attr_hs_color",
            hs_color_list(self),
            self._update_color("_attr_hs_color", ColorMode.HS),
            render_complex=True,
        )

        # Setup RGB Colors
        for option, attribute, length, colormode in (
            (CONF_RGB, "_attr_rgb_color", 3, ColorMode.RGB),
            (CONF_RGBW, "_attr_rgbw_color", 4, ColorMode.RGBW),
            (CONF_RGBWW, "_attr_rgbww_color", 5, ColorMode.RGBWW),
        ):
            self.setup_template(
                option,
                attribute,
                rgb_color_list(self, option, length),
                self._update_color(attribute, colormode),
                render_complex=True,
            )

        # Setup Effect templates
        self.setup_template(
            CONF_EFFECT_LIST,
            "_attr_effect_list",
            template_validators.list_of_strings(
                self, CONF_EFFECT_LIST, none_on_empty=True
            ),
            render_complex=True,
        )
        self.setup_template(
            CONF_EFFECT,
            "_attr_effect",
            template_validators.item_in_list(
                self, "_attr_effect", "_attr_effect_list", CONF_EFFECT_LIST
            ),
        )

        # Min/Max temperature templates
        self.setup_template(
            CONF_MAX_MIREDS,
            "_attr_max_color_temp_kelvin",
            template_validators.number(self, CONF_MAX_MIREDS),
            self._update_max_mireds,
        )
        self.setup_template(
            CONF_MIN_MIREDS,
            "_attr_min_color_temp_kelvin",
            template_validators.number(self, CONF_MIN_MIREDS),
            self._update_min_mireds,
        )

        # Transition
        self.setup_template(
            CONF_SUPPORTS_TRANSITION,
            "_supports_transition_template",
            template_validators.boolean(self, CONF_SUPPORTS_TRANSITION),
            self._update_supports_transition,
        )

        # Stored values for template attributes
        self._supports_transition = False

        color_modes = {ColorMode.ONOFF}
        for action_id, color_mode in (
            (CONF_ON_ACTION, None),
            (CONF_OFF_ACTION, None),
            (CONF_EFFECT_ACTION, None),
            (CONF_TEMPERATURE_ACTION, ColorMode.COLOR_TEMP),
            (CONF_LEVEL_ACTION, ColorMode.BRIGHTNESS),
            (CONF_HS_ACTION, ColorMode.HS),
            (CONF_RGB_ACTION, ColorMode.RGB),
            (CONF_RGBW_ACTION, ColorMode.RGBW),
            (CONF_RGBWW_ACTION, ColorMode.RGBWW),
        ):
            if (action_config := config.get(action_id)) is not None:
                self.add_script(action_id, action_config, name, DOMAIN)
                if color_mode:
                    color_modes.add(color_mode)

        self._attr_supported_color_modes = filter_supported_color_modes(color_modes)
        if len(self._attr_supported_color_modes) > 1:
            self._attr_color_mode = ColorMode.UNKNOWN
        if len(self._attr_supported_color_modes) == 1:
            self._attr_color_mode = next(iter(self._attr_supported_color_modes))

        self._attr_supported_features = LightEntityFeature(0)
        if self._action_scripts.get(CONF_EFFECT_ACTION):
            self._attr_supported_features |= LightEntityFeature.EFFECT
        if self._supports_transition is True:
            self._attr_supported_features |= LightEntityFeature.TRANSITION