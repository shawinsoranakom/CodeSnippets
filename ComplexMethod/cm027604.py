def _template_changed_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        """Check if condition is correct and run action."""
        track_result = updates.pop()

        template = track_result.template
        last_result = track_result.last_result
        result = track_result.result

        if isinstance(result, TemplateError):
            _LOGGER.error(
                "Error while processing template: %s",
                template.template,
                exc_info=result,
            )
            return

        if (
            not isinstance(last_result, TemplateError)
            and result_as_boolean(last_result)
        ) or not result_as_boolean(result):
            return

        hass.async_run_hass_job(
            job,
            event and event.data["entity_id"],
            event and event.data["old_state"],
            event and event.data["new_state"],
        )