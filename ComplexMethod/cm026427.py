def _handle_results(
        self,
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        """Call back the results to the attributes."""
        if event:
            self.async_set_context(event.context)

        entity_id = event and event.data["entity_id"]

        if entity_id and entity_id == self.entity_id:
            self._self_ref_update_count += 1
        else:
            self._self_ref_update_count = 0

        if self._self_ref_update_count > len(self._template_attrs):
            for update in updates:
                _LOGGER.warning(
                    (
                        "Template loop detected while processing event: %s, skipping"
                        " template render for Template[%s]"
                    ),
                    event,
                    update.template.template,
                )
            return

        errors = []
        for update in updates:
            for template_attr in self._template_attrs[update.template]:
                template_attr.handle_result(
                    event, update.template, update.last_result, update.result
                )
                if isinstance(update.result, TemplateError):
                    errors.append(update.result)

        if not self._preview_callback:
            self.async_write_ha_state()
            return

        if errors:
            self._preview_callback(None, None, None, str(errors[-1]))
            return

        try:
            calculated_state = self._async_calculate_state()
            validate_state(calculated_state.state)
        except Exception as err:  # noqa: BLE001
            self._preview_callback(None, None, None, str(err))
        else:
            assert self._template_result_info
            self._preview_callback(
                calculated_state.state,
                calculated_state.attributes,
                self._template_result_info.listeners,
                None,
            )