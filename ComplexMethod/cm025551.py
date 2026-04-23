async def async_step_rules(
        self, user_input: dict[str, Any] | None = None, rule_id: str | None = None
    ) -> ConfigFlowResult:
        """Handle options flow for detection rules."""
        if rule_id is not None:
            self._conf_rule_id = rule_id if rule_id != RULES_NEW_ID else None
            return self._async_rules_form(rule_id)

        if user_input is not None:
            rule_id = user_input.get(CONF_RULE_ID, self._conf_rule_id)
            if rule_id:
                if user_input.get(CONF_RULE_DELETE, False):
                    self._state_det_rules.pop(rule_id)
                elif det_rule := user_input.get(CONF_RULE_VALUES):
                    state_det_rule = _validate_state_det_rules(det_rule)
                    if state_det_rule is None:
                        return self._async_rules_form(
                            rule_id=self._conf_rule_id or RULES_NEW_ID,
                            default_id=rule_id,
                            errors={"base": "invalid_det_rules"},
                        )
                    self._state_det_rules[rule_id] = state_det_rule

        return await self.async_step_init()