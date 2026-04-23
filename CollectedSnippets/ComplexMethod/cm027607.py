def _refresh(
        self,
        event: Event[EventStateChangedData] | None,
        track_templates: Iterable[TrackTemplate] | None = None,
        replayed: bool | None = False,
    ) -> None:
        """Refresh the template.

        The event is the state_changed event that caused the refresh
        to be considered.

        track_templates is an optional list of TrackTemplate objects
        to refresh.  If not provided, all tracked templates will be
        considered.

        replayed is True if the event is being replayed because the
        rate limit was hit.
        """
        updates: list[TrackTemplateResult] = []
        info_changed = False
        now = event.time_fired_timestamp if not replayed and event else time.time()

        block_updates = False
        super_template = self._track_templates[0] if self._has_super_template else None

        track_templates = track_templates or self._track_templates

        # Update the super template first
        if super_template is not None:
            update = self._render_template_if_ready(super_template, now, event)
            info_changed |= self._apply_update(updates, update, super_template.template)

            if isinstance(update, TrackTemplateResult):
                super_result = update.result
            else:
                super_result = self._last_result.get(super_template.template)

            # If the super template did not render to True, don't update other templates
            if (
                super_result is not None
                and self._super_template_as_boolean(super_result) is not True
            ):
                block_updates = True

            if (
                isinstance(update, TrackTemplateResult)
                and self._super_template_as_boolean(update.last_result) is not True
                and self._super_template_as_boolean(update.result) is True
            ):
                # Super template changed from not True to True, force re-render
                # of all templates in the group
                event = None
                track_templates = self._track_templates

        # Then update the remaining templates unless blocked by the super template
        if not block_updates:
            for track_template_ in track_templates:
                if track_template_ == super_template:
                    continue

                update = self._render_template_if_ready(track_template_, now, event)
                info_changed |= self._apply_update(
                    updates, update, track_template_.template
                )

        if info_changed:
            assert self._track_state_changes
            self._track_state_changes.async_update_listeners(
                _render_infos_to_track_states(
                    [
                        _suppress_domain_all_in_render_info(info)
                        if self._rate_limit.async_has_timer(template)
                        else info
                        for template, info in self._info.items()
                    ]
                )
            )
            _LOGGER.debug(
                (
                    "Template group %s listens for %s, re-render blocked by super"
                    " template: %s"
                ),
                self._track_templates,
                self.listeners,
                block_updates,
            )

        if not updates:
            return

        for track_result in updates:
            self._last_result[track_result.template] = track_result.result

        self.hass.async_run_hass_job(self._job, event, updates)