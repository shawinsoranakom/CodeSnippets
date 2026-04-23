def _update_from_device(self) -> None:
        """Update from device."""
        if self._attr_supported_color_modes is None:
            # work out what (color)features are supported
            supported_color_modes = {ColorMode.ONOFF}
            # brightness support
            if self._entity_info.endpoint.has_attribute(
                None, clusters.LevelControl.Attributes.CurrentLevel
            ) and self._entity_info.endpoint.device_types != {device_types.OnOffLight}:
                # We need to filter out the OnOffLight device type here because
                # that can have an optional LevelControl cluster present
                # which we should ignore.
                supported_color_modes.add(ColorMode.BRIGHTNESS)
                self._supports_brightness = True
            # colormode(s)
            if self._entity_info.endpoint.has_attribute(
                None, clusters.ColorControl.Attributes.ColorMode
            ) and self._entity_info.endpoint.has_attribute(
                None, clusters.ColorControl.Attributes.ColorCapabilities
            ):
                capabilities = self.get_matter_attribute_value(
                    clusters.ColorControl.Attributes.ColorCapabilities
                )

                assert capabilities is not None

                if (
                    capabilities
                    & clusters.ColorControl.Bitmaps.ColorCapabilitiesBitmap.kHueSaturation
                ):
                    supported_color_modes.add(ColorMode.HS)
                    self._supports_color = True

                if (
                    capabilities
                    & clusters.ColorControl.Bitmaps.ColorCapabilitiesBitmap.kXy
                ):
                    supported_color_modes.add(ColorMode.XY)
                    self._supports_color = True

                if (
                    capabilities
                    & clusters.ColorControl.Bitmaps.ColorCapabilitiesBitmap.kColorTemperature
                ):
                    supported_color_modes.add(ColorMode.COLOR_TEMP)
                    self._supports_color_temperature = True
                    min_mireds = self.get_matter_attribute_value(
                        clusters.ColorControl.Attributes.ColorTempPhysicalMinMireds
                    )
                    if min_mireds > 0:
                        self._attr_max_color_temp_kelvin = (
                            color_util.color_temperature_mired_to_kelvin(min_mireds)
                        )
                    max_mireds = self.get_matter_attribute_value(
                        clusters.ColorControl.Attributes.ColorTempPhysicalMaxMireds
                    )
                    if max_mireds > 0:
                        self._attr_min_color_temp_kelvin = (
                            color_util.color_temperature_mired_to_kelvin(max_mireds)
                        )

            supported_color_modes = filter_supported_color_modes(supported_color_modes)
            self._attr_supported_color_modes = supported_color_modes
            self._check_transition_blocklist()
            # flag support for transition as soon as we support setting brightness and/or color
            if (
                supported_color_modes != {ColorMode.ONOFF}
                and not self._transitions_disabled
            ):
                self._attr_supported_features |= LightEntityFeature.TRANSITION

            LOGGER.debug(
                "Supported color modes: %s for %s",
                self._attr_supported_color_modes,
                self.entity_id,
            )

        # set current values
        self._attr_is_on = self.get_matter_attribute_value(
            clusters.OnOff.Attributes.OnOff
        )

        if self._supports_brightness:
            self._attr_brightness = self._get_brightness()

        if (
            self._supports_color_temperature
            and (color_temperature := self._get_color_temperature()) > 0
        ):
            self._attr_color_temp_kelvin = color_util.color_temperature_mired_to_kelvin(
                color_temperature
            )

        if self._supports_color:
            self._attr_color_mode = color_mode = self._get_color_mode()
            if (
                ColorMode.HS in self._attr_supported_color_modes
                and color_mode == ColorMode.HS
            ):
                self._attr_hs_color = self._get_hs_color()
            elif (
                ColorMode.XY in self._attr_supported_color_modes
                and color_mode == ColorMode.XY
            ):
                self._attr_xy_color = self._get_xy_color()
        elif self._supports_color_temperature:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif self._supports_brightness:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF