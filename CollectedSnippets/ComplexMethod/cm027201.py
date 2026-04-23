async def _async_update_data(self) -> UnifiAccessData:
        """Fetch all doors and emergency status from the API."""
        try:
            async with asyncio.timeout(10):
                doors, emergency = await asyncio.gather(
                    self.client.get_doors(),
                    self.client.get_emergency_status(),
                )
        except ApiAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except ApiConnectionError as err:
            raise UpdateFailed(f"Error connecting to API: {err}") from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed("Timeout communicating with UniFi Access API") from err

        previous_lock_rules = self.data.door_lock_rules.copy() if self.data else {}
        door_lock_rules: dict[str, DoorLockRuleStatus] = {}
        unconfirmed_lock_rule_doors: set[str] = set()
        lock_rule_support_complete = True
        try:
            async with asyncio.timeout(10):
                lock_rule_results = await asyncio.gather(
                    *(self._async_get_door_lock_rule(door.id) for door in doors),
                    return_exceptions=True,
                )
        except TimeoutError as err:
            lock_rule_results = [err] * len(doors)
        for door, result in zip(doors, lock_rule_results, strict=True):
            if isinstance(result, DoorLockRuleStatus):
                door_lock_rules[door.id] = result
                continue

            if result is None:
                continue

            lock_rule_support_complete = False
            _LOGGER.debug("Could not fetch door lock rule for %s: %s", door.id, result)
            if door.id in previous_lock_rules:
                door_lock_rules[door.id] = previous_lock_rules[door.id]
            else:
                unconfirmed_lock_rule_doors.add(door.id)

        supports_lock_rules = bool(door_lock_rules) or bool(unconfirmed_lock_rule_doors)

        current_ids = {door.id for door in doors} | {self.config_entry.entry_id}
        self._remove_stale_devices(current_ids)

        current_door_ids = {door.id for door in doors}
        self._device_to_door = {
            dev_id: door_id
            for dev_id, door_id in self._device_to_door.items()
            if door_id in current_door_ids
        }

        return UnifiAccessData(
            doors={door.id: door for door in doors},
            emergency=emergency,
            door_lock_rules=door_lock_rules,
            unconfirmed_lock_rule_doors=unconfirmed_lock_rule_doors,
            supports_lock_rules=supports_lock_rules,
            lock_rule_support_complete=lock_rule_support_complete,
            door_thumbnails={
                door.id: ThumbnailInfo(
                    url=door.door_thumbnail,
                    door_thumbnail_last_update=door.door_thumbnail_last_update,
                )
                for door in doors
                if door.door_thumbnail is not None
                and door.door_thumbnail_last_update is not None
            },
        )