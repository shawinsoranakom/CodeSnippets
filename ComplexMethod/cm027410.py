def _update_from_data(self) -> None:
        """Get the latest state of the sensor and update activity."""
        detail = self._detail
        if lock_activity := self._get_latest({ActivityType.LOCK_OPERATION}):
            self._attr_changed_by = lock_activity.operated_by
        lock_activity_without_operator = self._get_latest(
            {ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR}
        )
        if latest_activity := get_latest_activity(
            lock_activity_without_operator, lock_activity
        ):
            if latest_activity.was_pushed:
                self._detail.set_online(True)
            update_lock_detail_from_activity(detail, latest_activity)

        if bridge_activity := self._get_latest({ActivityType.BRIDGE_OPERATION}):
            update_lock_detail_from_activity(detail, bridge_activity)

        self._update_lock_status_from_detail()
        lock_status = self._lock_status
        if lock_status is None or lock_status is LockStatus.UNKNOWN:
            self._attr_is_locked = None
        else:
            self._attr_is_locked = lock_status is LockStatus.LOCKED
        self._attr_is_jammed = lock_status is LockStatus.JAMMED
        self._attr_is_locking = lock_status is LockStatus.LOCKING
        self._attr_is_unlocking = lock_status in (
            LockStatus.UNLOCKING,
            LockStatus.UNLATCHING,
        )
        self._attr_extra_state_attributes = {ATTR_BATTERY_LEVEL: detail.battery_level}
        if keypad := detail.keypad:
            self._attr_extra_state_attributes["keypad_battery_level"] = (
                keypad.battery_level
            )