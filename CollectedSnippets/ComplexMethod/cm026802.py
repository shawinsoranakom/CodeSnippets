def _configure_hvac_modes(self, state: State) -> None:
        """Configure target mode characteristics."""
        # This cannot be none OR an empty list
        hc_modes = state.attributes.get(ATTR_HVAC_MODES) or DEFAULT_HVAC_MODES
        # Determine available modes for this entity,
        # Prefer HEAT_COOL over AUTO and COOL over FAN_ONLY, DRY
        #
        # HEAT_COOL is preferred over auto because HomeKit Accessory Protocol describes
        # heating or cooling comes on to maintain a target temp which is closest to
        # the Home Assistant spec
        #
        # HVACMode.HEAT_COOL: The device supports heating/cooling to a range
        self.hc_homekit_to_hass = {
            c: s
            for s, c in HC_HASS_TO_HOMEKIT.items()
            if (
                s in hc_modes
                and not (
                    (s == HVACMode.AUTO and HVACMode.HEAT_COOL in hc_modes)
                    or (
                        s in (HVACMode.DRY, HVACMode.FAN_ONLY)
                        and HVACMode.COOL in hc_modes
                    )
                )
            )
        }
        self.hc_hass_to_homekit = {k: v for v, k in self.hc_homekit_to_hass.items()}