async def async_added_to_hass(self) -> None:
        """Restore ATTR_CHANGED_BY on startup since it is likely no longer in the activity log."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        last_sensor_state = await self.async_get_last_sensor_data()
        if (
            not last_state
            or not last_sensor_state
            or last_state.state == STATE_UNAVAILABLE
        ):
            return

        self._attr_native_value = last_sensor_state.native_value
        last_attrs = last_state.attributes
        if ATTR_ENTITY_PICTURE in last_attrs:
            self._attr_entity_picture = last_attrs[ATTR_ENTITY_PICTURE]
        if ATTR_OPERATION_REMOTE in last_attrs:
            self._operated_remote = last_attrs[ATTR_OPERATION_REMOTE]
        if ATTR_OPERATION_KEYPAD in last_attrs:
            self._operated_keypad = last_attrs[ATTR_OPERATION_KEYPAD]
        if ATTR_OPERATION_MANUAL in last_attrs:
            self._operated_manual = last_attrs[ATTR_OPERATION_MANUAL]
        if ATTR_OPERATION_TAG in last_attrs:
            self._operated_tag = last_attrs[ATTR_OPERATION_TAG]
        if ATTR_OPERATION_AUTORELOCK in last_attrs:
            self._operated_autorelock = last_attrs[ATTR_OPERATION_AUTORELOCK]