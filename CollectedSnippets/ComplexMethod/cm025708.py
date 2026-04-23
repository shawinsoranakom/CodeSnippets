def _update_presets(self) -> None:
        """Update preset modes and active preset."""
        # Check if the device supports presets feature before attempting to load.
        # Use the already computed supported features instead of re-reading
        # the FeatureMap attribute to keep a single source of truth and avoid
        # casting None when the attribute is temporarily unavailable.
        supported_features = self._attr_supported_features or 0
        if not (supported_features & ClimateEntityFeature.PRESET_MODE):
            # Device does not support presets, skip preset update
            self._preset_handle_by_name.clear()
            self._preset_name_by_handle.clear()
            self._attr_preset_modes = []
            self._attr_preset_mode = None
            return

        self._matter_presets = (
            self.get_matter_attribute_value(clusters.Thermostat.Attributes.Presets)
            or []
        )
        # Build preset mapping: use device-provided name if available, else generate unique name
        self._preset_handle_by_name.clear()
        self._preset_name_by_handle.clear()
        if self._matter_presets:
            used_names = set()
            for i, preset in enumerate(self._matter_presets, start=1):
                preset_translation = PRESET_SCENARIO_TO_HA_PRESET.get(
                    preset.presetScenario
                )
                if preset_translation:
                    preset_name = preset_translation.lower()
                else:
                    name = str(preset.name) if preset.name is not None else ""
                    name = name.strip()
                    if name:
                        preset_name = name
                    else:
                        # Ensure fallback name is unique
                        j = i
                        preset_name = f"Preset{j}"
                        while preset_name in used_names:
                            j += 1
                            preset_name = f"Preset{j}"
                used_names.add(preset_name)
                preset_handle = (
                    preset.presetHandle
                    if isinstance(preset.presetHandle, (bytes, type(None)))
                    else None
                )
                self._preset_handle_by_name[preset_name] = preset_handle
                self._preset_name_by_handle[preset_handle] = preset_name

        # Always include PRESET_NONE to allow users to clear the preset
        self._preset_handle_by_name[PRESET_NONE] = None
        self._preset_name_by_handle[None] = PRESET_NONE

        self._attr_preset_modes = list(self._preset_handle_by_name)

        # Update active preset mode
        active_preset_handle = self.get_matter_attribute_value(
            clusters.Thermostat.Attributes.ActivePresetHandle
        )
        self._attr_preset_mode = self._preset_name_by_handle.get(
            active_preset_handle, PRESET_NONE
        )