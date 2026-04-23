def async_update_state(self, state: EntityState) -> None:
        """Distribute an update of state information to the target."""
        key = state.key
        state_type = type(state)
        stale_state = self.stale_state
        current_state_by_type = self.state[state_type]
        current_state = current_state_by_type.get(key, _SENTINEL)
        subscription_key = (state_type, state.device_id, key)
        if (
            current_state == state
            and subscription_key not in stale_state
            and state_type not in (CameraState, Event)
            and not (
                state_type is SensorState
                and (platform_info := self.info.get(SensorInfo))
                and (entity_info := platform_info.get((state.device_id, state.key)))
                and (cast(SensorInfo, entity_info)).force_update
            )
        ):
            return
        stale_state.discard(subscription_key)
        current_state_by_type[key] = state
        if subscription := self.state_subscriptions.get(subscription_key):
            try:
                subscription()
            except Exception:
                # If we allow this exception to raise it will
                # make it all the way to data_received in aioesphomeapi
                # which will cause the connection to be closed.
                _LOGGER.exception("Error while calling subscription")