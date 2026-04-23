def check_light_on_dev_state_change(
        from_state: str, to_state: str, event: Event[EventStateChangedData]
    ) -> None:
        """Handle tracked device state changes."""
        event_data = event.data
        if (
            (old_state := event_data["old_state"]) is None
            or (new_state := event_data["new_state"]) is None
            or old_state.state != from_state
            or new_state.state != to_state
        ):
            return

        entity = event_data["entity_id"]
        lights_are_on = any_light_on()
        light_needed = not (lights_are_on or is_up(hass))

        # These variables are needed for the elif check
        now = dt_util.utcnow()
        start_point = calc_time_for_light_when_sunset()

        # Do we need lights?
        if light_needed:
            logger.info("Home coming event for %s. Turning lights on", entity)
            hass.async_create_task(
                hass.services.async_call(
                    LIGHT_DOMAIN,
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: light_ids, ATTR_PROFILE: light_profile},
                )
            )

        # Are we in the time span were we would turn on the lights
        # if someone would be home?
        # Check this by seeing if current time is later then the point
        # in time when we would start putting the lights on.
        elif start_point and start_point < now < get_astral_event_next(
            hass, SUN_EVENT_SUNSET
        ):
            # Check for every light if it would be on if someone was home
            # when the fading in started and turn it on if so
            for index, light_id in enumerate(light_ids):
                if now > start_point + index * LIGHT_TRANSITION_TIME:
                    hass.async_create_task(
                        hass.services.async_call(
                            LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: light_id}
                        )
                    )

                else:
                    # If this light didn't happen to be turned on yet so
                    # will all the following then, break.
                    break