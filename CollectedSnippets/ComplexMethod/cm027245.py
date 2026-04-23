def _async_listener() -> None:
            """Handle alarm creation and deletion after coordinator data update."""
            new_alarms: set[str] = set()
            received_alarms: set[str] = set()

            if coordinator.data["alarms"] and coordinator.available:
                received_alarms = set(coordinator.data["alarms"])
                new_alarms = received_alarms - coordinator.known_alarms
            removed_alarms = coordinator.known_alarms - received_alarms

            if new_alarms:
                for new_alarm in new_alarms:
                    coordinator.known_alarms.add(new_alarm)
                    _LOGGER.debug(
                        "Setting up alarm entity for alarm %s on player %s",
                        new_alarm,
                        coordinator.player,
                    )
                    async_add_entities([SqueezeBoxAlarmEntity(coordinator, new_alarm)])

            if removed_alarms and coordinator.available:
                for removed_alarm in removed_alarms:
                    _uid = f"{coordinator.player_uuid}_alarm_{removed_alarm}"
                    _LOGGER.debug(
                        "Alarm %s with unique_id %s needs to be deleted",
                        removed_alarm,
                        _uid,
                    )

                    entity_registry = er.async_get(hass)
                    _entity_id = entity_registry.async_get_entity_id(
                        Platform.SWITCH,
                        DOMAIN,
                        _uid,
                    )
                    if _entity_id:
                        entity_registry.async_remove(_entity_id)
                        coordinator.known_alarms.remove(removed_alarm)