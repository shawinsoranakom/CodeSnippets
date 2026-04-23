def _update_state(self, result):
        super()._update_state(result)

        if self._delay_cancel:
            self._delay_cancel()
            self._delay_cancel = None

        state: bool | None = None
        if result is not None and not isinstance(result, TemplateError):
            state = template.result_as_boolean(result)

        if state == self._attr_is_on:
            return

        # state without delay
        if (
            state is None
            or (state and not self._delay_on)
            or (not state and not self._delay_off)
        ):
            self._attr_is_on = state
            return

        @callback
        def _set_state(_):
            """Set state of template binary sensor."""
            self._attr_is_on = state
            self.async_write_ha_state()

        delay = (self._delay_on if state else self._delay_off).total_seconds()
        # state with delay. Cancelled if template result changes.
        self._delay_cancel = async_call_later(self.hass, delay, _set_state)