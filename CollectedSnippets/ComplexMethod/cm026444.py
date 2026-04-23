def _update_state(self, result):
        state: bool | None = None
        if result is not None:
            state = template.result_as_boolean(result)

        if state:
            delay = self._rendered.get(CONF_DELAY_ON) or self._delay_on
        else:
            delay = self._rendered.get(CONF_DELAY_OFF) or self._delay_off

        if (
            self._delay_cancel
            and delay
            and self._attr_is_on == self._last_delay_from
            and state == self._last_delay_to
        ):
            return

        self._cancel_delays()

        # state without delay.
        if self._attr_is_on == state or delay is None:
            self._set_state(state)
            return

        if not isinstance(delay, timedelta):
            try:
                delay = cv.positive_time_period(delay)
            except vol.Invalid as err:
                key = CONF_DELAY_ON if state else CONF_DELAY_OFF
                logging.getLogger(__name__).warning(
                    "Error rendering %s template: %s", key, err
                )
                return

        # state with delay. Cancelled if new trigger received
        self._last_delay_from = self._attr_is_on
        self._last_delay_to = state
        self._delay_cancel = async_call_later(
            self.hass, delay.total_seconds(), partial(self._set_state, state)
        )