def state_change_listener(event: Event[EventStateChangedData]) -> None:
        """Handle specific state changes."""
        # Skip if the event's source does not match the trigger's source.
        from_state = event.data["old_state"]
        to_state = event.data["new_state"]
        if not source_match(from_state, source) and not source_match(to_state, source):
            return

        if (zone_state := hass.states.get(zone_entity_id)) is None:
            _LOGGER.warning(
                "Unable to execute automation %s: Zone %s not found",
                trigger_info["name"],
                zone_entity_id,
            )
            return

        from_match = (
            zone_condition.zone(hass, zone_state, from_state) if from_state else False
        )
        to_match = (
            zone_condition.zone(hass, zone_state, to_state) if to_state else False
        )

        if (trigger_event == EVENT_ENTER and not from_match and to_match) or (
            trigger_event == EVENT_LEAVE and from_match and not to_match
        ):
            hass.async_run_hass_job(
                job,
                {
                    "trigger": {
                        **trigger_data,
                        "platform": "geo_location",
                        "source": source,
                        "entity_id": event.data["entity_id"],
                        "from_state": from_state,
                        "to_state": to_state,
                        "zone": zone_state,
                        "event": trigger_event,
                        "description": f"geo_location - {source}",
                    }
                },
                event.context,
            )