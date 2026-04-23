def template_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        """Listen for state changes and calls action."""
        nonlocal delay_cancel, armed
        result = updates.pop().result

        if isinstance(result, exceptions.TemplateError):
            _LOGGER.warning(
                "Error evaluating 'template' trigger for '%s': %s",
                trigger_info["name"],
                result,
            )
            return

        if delay_cancel:
            delay_cancel()
            delay_cancel = None

        if not result_as_boolean(result):
            armed = True
            return

        # Only fire when previously armed.
        if not armed:
            return

        # Fire!
        armed = False

        entity_id = event and event.data["entity_id"]
        from_s = event and event.data["old_state"]
        to_s = event and event.data["new_state"]

        if entity_id is not None:
            description = f"{entity_id} via template"
        else:
            description = "time change or manual update via template"

        template_variables = {
            "platform": platform_type,
            "entity_id": entity_id,
            "from_state": from_s,
            "to_state": to_s,
        }
        trigger_variables = {
            **trigger_data,
            "for": time_delta,
            "description": description,
        }

        @callback
        def call_action(*_: Any) -> None:
            """Call action with right context."""
            nonlocal trigger_variables
            hass.async_run_hass_job(
                job,
                {"trigger": {**template_variables, **trigger_variables}},
                (to_s.context if to_s else None),
            )

        if not time_delta:
            call_action()
            return

        data = {"trigger": template_variables}
        period_variables = {**variables, **data}

        try:
            period: timedelta = cv.positive_time_period(
                template.render_complex(time_delta, period_variables)
            )
        except (exceptions.TemplateError, vol.Invalid) as ex:
            _LOGGER.error(
                "Error rendering '%s' for template: %s", trigger_info["name"], ex
            )
            return

        trigger_variables["for"] = period

        delay_cancel = async_call_later(hass, period.total_seconds(), call_action)