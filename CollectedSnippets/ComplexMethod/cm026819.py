def __init__(self, *args: Any, category: int = CATEGORY_FAN) -> None:
        """Initialize a new Fan accessory object."""
        super().__init__(*args, category=category)
        self.chars: list[str] = []
        state = self.hass.states.get(self.entity_id)
        assert state
        self._reload_on_change_attrs.extend(
            (
                ATTR_PERCENTAGE_STEP,
                ATTR_PRESET_MODES,
            )
        )

        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        percentage_step = state.attributes.get(ATTR_PERCENTAGE_STEP, 1)
        self.preset_modes: list[str] | None = state.attributes.get(ATTR_PRESET_MODES)

        if features & FanEntityFeature.DIRECTION:
            self.chars.append(CHAR_ROTATION_DIRECTION)
        if features & FanEntityFeature.OSCILLATE:
            self.chars.append(CHAR_SWING_MODE)
        if features & FanEntityFeature.SET_SPEED:
            self.chars.append(CHAR_ROTATION_SPEED)

        serv_fan = self.create_services()

        self.char_direction = None
        self.char_speed = None
        self.char_swing = None
        self.char_target_fan_state = None
        self.preset_mode_chars = {}

        if CHAR_ROTATION_DIRECTION in self.chars:
            self.char_direction = serv_fan.configure_char(
                CHAR_ROTATION_DIRECTION, value=0
            )

        if CHAR_ROTATION_SPEED in self.chars:
            # Initial value is set to 100 because 0 is a special value (off). 100 is
            # an arbitrary non-zero value. It is updated immediately by async_update_state
            # to set to the correct initial value.
            self.char_speed = serv_fan.configure_char(
                CHAR_ROTATION_SPEED,
                value=100,
                properties={PROP_MIN_STEP: percentage_step},
            )

        if (
            self.preset_modes
            and len(self.preset_modes) == 1
            # NOTE: This would be missing for air purifiers
            and CHAR_TARGET_FAN_STATE in self.chars
        ):
            self.char_target_fan_state = serv_fan.configure_char(
                CHAR_TARGET_FAN_STATE,
                value=0,
            )
        elif self.preset_modes:
            for preset_mode in self.preset_modes:
                if not self.should_add_preset_mode_switch(preset_mode):
                    continue

                preset_serv = self.add_preload_service(
                    SERV_SWITCH,
                    [CHAR_NAME, CHAR_CONFIGURED_NAME],
                    unique_id=preset_mode,
                )
                serv_fan.add_linked_service(preset_serv)
                preset_serv.configure_char(
                    CHAR_NAME,
                    value=cleanup_name_for_homekit(
                        f"{self.display_name} {preset_mode}"
                    ),
                )
                preset_serv.configure_char(
                    CHAR_CONFIGURED_NAME, value=cleanup_name_for_homekit(preset_mode)
                )

                def setter_callback(value: int, preset_mode: str = preset_mode) -> None:
                    self.set_preset_mode(value, preset_mode)

                self.preset_mode_chars[preset_mode] = preset_serv.configure_char(
                    CHAR_ON,
                    value=False,
                    setter_callback=setter_callback,
                )

        if CHAR_SWING_MODE in self.chars:
            self.char_swing = serv_fan.configure_char(CHAR_SWING_MODE, value=0)
        self.async_update_state(state)
        serv_fan.setter_callback = self.set_chars