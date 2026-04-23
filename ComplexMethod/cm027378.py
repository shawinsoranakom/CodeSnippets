def zone_automation_listener(zone_event: Event[EventStateChangedData]) -> None:
        """Listen for state changes and calls action."""
        entity = zone_event.data["entity_id"]
        from_s = zone_event.data["old_state"]
        to_s = zone_event.data["new_state"]

        if (from_s and not location.has_location(from_s)) or (
            to_s and not location.has_location(to_s)
        ):
            return

        if not (zone_state := hass.states.get(zone_entity_id)):
            _LOGGER.warning(
                (
                    "Automation '%s' is referencing non-existing zone '%s' in a zone"
                    " trigger"
                ),
                trigger_info["name"],
                zone_entity_id,
            )
            return

        from_match = condition.zone(hass, zone_state, from_s) if from_s else False
        to_match = condition.zone(hass, zone_state, to_s) if to_s else False

        if (event == EVENT_ENTER and not from_match and to_match) or (
            event == EVENT_LEAVE and from_match and not to_match
        ):
            description = f"{entity} {_EVENT_DESCRIPTION[event]} {zone_state.attributes[ATTR_FRIENDLY_NAME]}"
            hass.async_run_hass_job(
                job,
                {
                    "trigger": {
                        **trigger_data,
                        "platform": platform_type,
                        "entity_id": entity,
                        "from_state": from_s,
                        "to_state": to_s,
                        "zone": zone_state,
                        "event": event,
                        "description": description,
                    }
                },
                to_s.context if to_s else None,
            )