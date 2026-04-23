def __init__(self, api: PyAxencoAPI, device: dict[str, Any]) -> None:
        """Initialize the MyNeoClimate entity."""
        self._api = api
        self._device = device
        self._device_id: str = device["_id"]
        model = device.get("model")
        name = device.get("name") or self._device_id

        self._attr_unique_id = self._device_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=name,
            manufacturer="Axenco",
            model=model,
        )

        connected = bool(device.get("connected", False))
        self._attr_available = connected
        self._unavailable_logged: bool = False

        state = device.get("state", {})
        self._is_sub_device = model in SUPPORTED_SUB_MODELS
        self._parents = device.get("parents") or {}
        if model in PRESET_MODE_MODELS:
            self._attr_preset_modes = PRESET_MODE_MODELS[model]
        else:
            default_presets = [p.key for p in Preset]
            _LOGGER.warning(
                "Model %s not found in PRESET_MODE_MODELS, using default presets %s",
                model,
                default_presets,
            )
            self._attr_preset_modes = default_presets
        self._attr_min_temp = state.get("comfLimitMin", 7)
        self._attr_max_temp = state.get("comfLimitMax", 30)
        self._attr_current_temperature = state.get("currentTemp")
        self._attr_target_temperature = (
            state.get("targetTemp")
            if self._is_sub_device
            else state.get("overrideTemp")
        )
        target_mode = state.get("targetMode")
        if isinstance(target_mode, int):
            self._attr_preset_mode = REVERSE_PRESET_MODE_MAP.get(target_mode)
        else:
            self._attr_preset_mode = None
        self._last_preset_mode: str | None = (
            self._attr_preset_mode
            if self._attr_preset_mode and self._attr_preset_mode != "standby"
            else None
        )
        if model == "NTD" and state.get("changeOverUser") == 1:
            self._attr_hvac_modes = [HVACMode.COOL, HVACMode.OFF]
            self._attr_hvac_mode = (
                HVACMode.OFF
                if PRESET_MODE_MAP.get(self._attr_preset_mode or "") == 4
                else HVACMode.COOL
            )
        else:
            self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
            self._attr_hvac_mode = (
                HVACMode.OFF
                if PRESET_MODE_MAP.get(self._attr_preset_mode or "") == 4
                else HVACMode.HEAT
            )