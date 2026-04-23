def _on_static_info_update(self, static_info: EntityInfo) -> None:
        """Set attrs from static info."""
        super()._on_static_info_update(static_info)
        static_info = self._static_info
        feature = 0
        if static_info.supported_features & EspHomeACPFeatures.ARM_HOME:
            feature |= AlarmControlPanelEntityFeature.ARM_HOME
        if static_info.supported_features & EspHomeACPFeatures.ARM_AWAY:
            feature |= AlarmControlPanelEntityFeature.ARM_AWAY
        if static_info.supported_features & EspHomeACPFeatures.ARM_NIGHT:
            feature |= AlarmControlPanelEntityFeature.ARM_NIGHT
        if static_info.supported_features & EspHomeACPFeatures.TRIGGER:
            feature |= AlarmControlPanelEntityFeature.TRIGGER
        if static_info.supported_features & EspHomeACPFeatures.ARM_CUSTOM_BYPASS:
            feature |= AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS
        if static_info.supported_features & EspHomeACPFeatures.ARM_VACATION:
            feature |= AlarmControlPanelEntityFeature.ARM_VACATION
        self._attr_supported_features = AlarmControlPanelEntityFeature(feature)
        self._attr_code_format = (
            CodeFormat.NUMBER if static_info.requires_code else None
        )
        self._attr_code_arm_required = bool(static_info.requires_code_to_arm)