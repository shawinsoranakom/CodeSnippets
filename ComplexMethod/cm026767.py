def state_automation_listener(event: Event[EventStateChangedData]) -> None:
        """Listen for state changes and calls action."""
        entity = event.data["entity_id"]
        from_s = event.data["old_state"]
        to_s = event.data["new_state"]

        if from_s is None:
            old_value = None
        elif attribute is None:
            old_value = from_s.state
        else:
            old_value = from_s.attributes.get(attribute)

        if to_s is None:
            new_value = None
        elif attribute is None:
            new_value = to_s.state
        else:
            new_value = to_s.attributes.get(attribute)

        # When we listen for state changes with `match_all`, we
        # will trigger even if just an attribute changes. When
        # we listen to just an attribute, we should ignore all
        # other attribute changes.
        if attribute is not None and old_value == new_value:
            return

        if (
            not match_from_state(old_value)
            or not match_to_state(new_value)
            or (not match_all and old_value == new_value)
        ):
            return

        @callback
        def call_action() -> None:
            """Call action with right context."""
            hass.async_run_hass_job(
                job,
                {
                    "trigger": {
                        **trigger_data,
                        "platform": platform_type,
                        "entity_id": entity,
                        "from_state": from_s,
                        "to_state": to_s,
                        "for": time_delta if not time_delta else period[entity],
                        "attribute": attribute,
                        "description": f"state of {entity}",
                    }
                },
                event.context,
            )

        if not time_delta:
            call_action()
            return

        data = {
            "trigger": {
                "platform": "state",
                "entity_id": entity,
                "from_state": from_s,
                "to_state": to_s,
            }
        }
        variables = {**_variables, **data}

        try:
            period[entity] = cv.positive_time_period(
                template.render_complex(time_delta, variables)
            )
        except (exceptions.TemplateError, vol.Invalid) as ex:
            _LOGGER.error(
                "Error rendering '%s' for template: %s", trigger_info["name"], ex
            )
            return

        def _check_same_state(_: str, _2: State | None, new_st: State | None) -> bool:
            if new_st is None:
                return False

            cur_value: str | None
            if attribute is None:
                cur_value = new_st.state
            else:
                cur_value = new_st.attributes.get(attribute)

            if CONF_FROM in config and CONF_TO not in config:
                return cur_value != old_value

            return cur_value == new_value

        unsub_track_same[entity] = async_track_same_state(
            hass,
            period[entity],
            call_action,
            _check_same_state,
            entity_ids=entity,
        )