def add_bridge_accessory(self, state: State) -> HomeAccessory | None:
        """Try adding accessory to bridge if configured beforehand."""
        assert self.driver is not None

        if self._would_exceed_max_devices(state.entity_id):
            return None

        if state_needs_accessory_mode(state):
            if self._exclude_accessory_mode:
                return None
            _LOGGER.warning(
                (
                    "The bridge %s has entity %s. For best performance, "
                    "and to prevent unexpected unavailability, create and "
                    "pair a separate HomeKit instance in accessory mode for "
                    "this entity"
                ),
                self._name,
                state.entity_id,
            )

        assert self.aid_storage is not None
        assert self.bridge is not None
        aid = self.aid_storage.get_or_allocate_aid_for_entity_id(state.entity_id)
        conf = self._config.get(state.entity_id, {}).copy()
        # If an accessory cannot be created or added due to an exception
        # of any kind (usually in pyhap) it should not prevent
        # the rest of the accessories from being created
        try:
            acc = get_accessory(self.hass, self.driver, state, aid, conf)
            if acc is not None:
                self.bridge.add_accessory(acc)
                return acc
        except Exception:
            _LOGGER.exception(
                "Failed to create a HomeKit accessory for %s", state.entity_id
            )
        return None