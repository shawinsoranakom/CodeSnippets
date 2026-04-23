def _process_door_update(
        self,
        door_id: str,
        ws_state: LocationUpdateState | V2LocationState | None,
        thumbnail: ThumbnailInfo | None = None,
    ) -> None:
        """Process a door state update from WebSocket."""
        if self.data is None or door_id not in self.data.doors:
            return

        if ws_state is None and thumbnail is None:
            return

        current_door = self.data.doors[door_id]
        updates: dict[str, object] = {}
        door_lock_rules = self.data.door_lock_rules
        unconfirmed_lock_rule_doors = self.data.unconfirmed_lock_rule_doors.copy()
        current_lock_rule = door_lock_rules.get(door_id)
        updated_lock_rule = current_lock_rule
        lock_rule_updated = False
        if ws_state is not None:
            if ws_state.dps is not None:
                updates["door_position_status"] = ws_state.dps
            if ws_state.lock == "locked":
                updates["door_lock_relay_status"] = DoorLockRelayStatus.LOCK
            elif ws_state.lock == "unlocked":
                updates["door_lock_relay_status"] = DoorLockRelayStatus.UNLOCK

            if "remain_lock" in ws_state.model_fields_set:
                lock_rule_updated = True
                updated_lock_rule = (
                    ws_state.remain_lock.to_door_lock_rule_status()
                    if ws_state.remain_lock is not None
                    else DoorLockRuleStatus()
                )
            elif "remain_unlock" in ws_state.model_fields_set:
                lock_rule_updated = True
                updated_lock_rule = (
                    ws_state.remain_unlock.to_door_lock_rule_status()
                    if ws_state.remain_unlock is not None
                    else DoorLockRuleStatus()
                )

        if (
            not updates
            and thumbnail is None
            and (not lock_rule_updated or updated_lock_rule == current_lock_rule)
        ):
            return

        updated_door = current_door.with_updates(**updates) if updates else current_door
        new_thumbnails = (
            {**self.data.door_thumbnails, door_id: thumbnail}
            if thumbnail is not None
            else self.data.door_thumbnails
        )
        supports_lock_rules = self.data.supports_lock_rules
        if lock_rule_updated and (
            updated_lock_rule != current_lock_rule
            or door_id in unconfirmed_lock_rule_doors
        ):
            door_lock_rules = {
                **door_lock_rules,
                door_id: updated_lock_rule or DoorLockRuleStatus(),
            }
            unconfirmed_lock_rule_doors.discard(door_id)
            supports_lock_rules = True

        self.async_set_updated_data(
            replace(
                self.data,
                doors={**self.data.doors, door_id: updated_door},
                door_lock_rules=door_lock_rules,
                unconfirmed_lock_rule_doors=unconfirmed_lock_rule_doors,
                supports_lock_rules=supports_lock_rules,
                door_thumbnails=new_thumbnails,
            )
        )