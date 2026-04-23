def _calculate_features(self) -> None:
        """Calculate features for HA Vacuum platform."""
        accepted_operational_commands: list[int] = self.get_matter_attribute_value(
            clusters.RvcOperationalState.Attributes.AcceptedCommandList
        )
        service_area_feature_map: int | None = self.get_matter_attribute_value(
            clusters.ServiceArea.Attributes.FeatureMap
        )

        # In principle the feature set should not change, except for accepted
        # commands and service area feature map.
        if (
            self._last_accepted_commands == accepted_operational_commands
            and self._last_service_area_feature_map == service_area_feature_map
        ):
            return

        self._last_accepted_commands = accepted_operational_commands
        self._last_service_area_feature_map = service_area_feature_map
        supported_features: VacuumEntityFeature = VacuumEntityFeature(0)
        supported_features |= VacuumEntityFeature.START
        supported_features |= VacuumEntityFeature.STATE
        supported_features |= VacuumEntityFeature.STOP

        # optional identify cluster = locate feature (value must be not None or 0)
        if self.get_matter_attribute_value(clusters.Identify.Attributes.IdentifyType):
            supported_features |= VacuumEntityFeature.LOCATE
        # create a map of supported run modes
        run_modes: list[clusters.RvcRunMode.Structs.ModeOptionStruct] = (
            self.get_matter_attribute_value(
                clusters.RvcRunMode.Attributes.SupportedModes
            )
        )
        self._supported_run_modes = {mode.mode: mode for mode in run_modes}
        # map operational state commands to vacuum features
        if (
            clusters.RvcOperationalState.Commands.Pause.command_id
            in accepted_operational_commands
        ):
            supported_features |= VacuumEntityFeature.PAUSE
        if (
            clusters.RvcOperationalState.Commands.GoHome.command_id
            in accepted_operational_commands
        ):
            supported_features |= VacuumEntityFeature.RETURN_HOME
        # Check if Map feature is enabled for clean area support
        if (
            service_area_feature_map is not None
            and service_area_feature_map & clusters.ServiceArea.Bitmaps.Feature.kMaps
        ):
            supported_features |= VacuumEntityFeature.CLEAN_AREA

        self._attr_supported_features = supported_features