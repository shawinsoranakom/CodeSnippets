def handle_ws_update(self, new_state: dict[str, Any]) -> None:
        """Handle WebSocket updates for the device."""
        if not new_state:
            return

        if "connected" in new_state:
            self._attr_available = new_state["connected"]
            if not self._attr_available:
                if not self._unavailable_logged:
                    _LOGGER.info("The entity %s is unavailable", self.entity_id)
                    self._unavailable_logged = True
            elif self._unavailable_logged:
                _LOGGER.info("The entity %s is back online", self.entity_id)
                self._unavailable_logged = False

        # Check for state updates using the description's state_key
        state_key = self.entity_description.state_key
        if state_key in new_state:
            mode = new_state.get(state_key)
            if mode is not None:
                self._attr_current_option = (
                    self.entity_description.reverse_preset_mode_map.get(mode)
                )

        self.async_write_ha_state()