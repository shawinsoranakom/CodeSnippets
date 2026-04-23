async def execute(self, command, data, params, challenge):
        """Execute an ArmDisarm command."""
        if params["arm"] and not params.get("cancel"):
            # If no arm level given, we we arm the first supported
            # level in state_to_support.
            if not (arm_level := params.get("armLevel")):
                arm_level = self._default_arm_state()

            if self.state.state == arm_level:
                raise SmartHomeError(ERR_ALREADY_ARMED, "System is already armed")
            if self.state.attributes["code_arm_required"]:
                _verify_pin_challenge(data, self.state, challenge)
            service = self.state_to_service[arm_level]
        # disarm the system without asking for code when
        # 'cancel' arming action is received while current status is pending
        elif (
            params["arm"]
            and params.get("cancel")
            and self.state.state == AlarmControlPanelState.PENDING
        ):
            service = SERVICE_ALARM_DISARM
        else:
            if self.state.state == AlarmControlPanelState.DISARMED:
                raise SmartHomeError(ERR_ALREADY_DISARMED, "System is already disarmed")
            _verify_pin_challenge(data, self.state, challenge)
            service = SERVICE_ALARM_DISARM

        await self.hass.services.async_call(
            alarm_control_panel.DOMAIN,
            service,
            {
                ATTR_ENTITY_ID: self.state.entity_id,
                ATTR_CODE: data.config.secure_devices_pin,
            },
            blocking=not self.config.should_report_state,
            context=data.context,
        )