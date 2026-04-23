def __init__(self, coordinator: OpenRGBCoordinator, device_key: str) -> None:
        """Initialize the OpenRGB light."""
        super().__init__(coordinator)
        self.device_key = device_key
        self._attr_unique_id = device_key

        device_name = coordinator.get_device_name(device_key)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_key)},
            name=device_name,
            manufacturer=self.device.metadata.vendor,
            model=f"{self.device.metadata.description} ({self.device.type.name})",
            sw_version=self.device.metadata.version,
            serial_number=self.device.metadata.serial,
            via_device=(DOMAIN, coordinator.entry_id),
        )

        modes = [mode.name for mode in self.device.modes]

        if self.device.metadata.description == "ASRock Polychrome USB Device":
            # https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/5145
            self._preferred_no_effect_mode = OpenRGBMode.STATIC
        else:
            # https://gitlab.com/CalcProgrammer1/OpenRGB/-/blob/c71cc4f18a54f83d388165ef2ab4c4ad3e980b89/RGBController/RGBController.cpp#L2075-2081
            self._preferred_no_effect_mode = (
                OpenRGBMode.DIRECT
                if OpenRGBMode.DIRECT in modes
                else OpenRGBMode.CUSTOM
                if OpenRGBMode.CUSTOM in modes
                else OpenRGBMode.STATIC
            )
        # Determine if the device supports being turned off through modes
        self._supports_off_mode = OpenRGBMode.OFF in modes
        # Determine which modes supports color
        self._supports_color_modes = [
            mode.name
            for mode in self.device.modes
            if check_if_mode_supports_color(mode)
        ]

        # Initialize effects from modes
        self._effect_to_mode = {}
        effects = []
        for mode in modes:
            if mode != OpenRGBMode.OFF and mode not in EFFECT_OFF_OPENRGB_MODES:
                effect_name = slugify(mode)
                effects.append(effect_name)
                self._effect_to_mode[effect_name] = mode

        if len(effects) > 0:
            self._supports_effects = True
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._attr_effect_list = [EFFECT_OFF, *effects]
        else:
            self._supports_effects = False

        self._attr_icon = DEVICE_TYPE_ICONS.get(self.device.type)

        self._update_attrs()