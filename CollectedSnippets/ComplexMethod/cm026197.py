def _async_validate_code(self, code: str | None, state: str) -> None:
        """Validate given code."""
        if (
            state != AlarmControlPanelState.DISARMED and not self.code_arm_required
        ) or self._code is None:
            return

        if isinstance(self._code, str):
            alarm_code = self._code
        else:
            alarm_code = self._code.async_render(
                parse_result=False, from_state=self._state, to_state=state
            )

        if not alarm_code or code == alarm_code:
            return

        current_context = (
            self._context if hasattr(self, "_context") and self._context else None
        )
        user_id_from_context = current_context.user_id if current_context else None

        self.hass.bus.async_fire(
            "manual_alarm_bad_code_attempt",
            {
                "entity_id": self.entity_id,
                "user_id": user_id_from_context,
                "target_state": state,
            },
        )

        raise ServiceValidationError(
            "Invalid alarm code provided",
            translation_domain=DOMAIN,
            translation_key="invalid_code",
        )