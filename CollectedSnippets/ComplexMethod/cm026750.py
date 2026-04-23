async def execute(self, command, data, params, challenge):
        """Execute an Open, close, Set position command."""
        domain = self.state.domain
        features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if domain in COVER_VALVE_DOMAINS:
            svc_params = {ATTR_ENTITY_ID: self.state.entity_id}
            should_verify = False
            if command == COMMAND_OPEN_CLOSE_RELATIVE:
                position = self.state.attributes.get(
                    COVER_VALVE_CURRENT_POSITION[domain]
                )
                if position is None:
                    raise SmartHomeError(
                        ERR_NOT_SUPPORTED,
                        "Current position not know for relative command",
                    )
                position = max(0, min(100, position + params["openRelativePercent"]))
            else:
                position = params["openPercent"]

            if position == 0:
                service = SERVICE_CLOSE_COVER_VALVE[domain]
                should_verify = False
            elif position == 100:
                service = SERVICE_OPEN_COVER_VALVE[domain]
                should_verify = True
            elif features & COVER_VALVE_SET_POSITION_FEATURE[domain]:
                service = SERVICE_SET_POSITION_COVER_VALVE[domain]
                if position > 0:
                    should_verify = True
                svc_params[COVER_VALVE_POSITION[domain]] = position
            else:
                raise SmartHomeError(
                    ERR_NOT_SUPPORTED, "No support for partial open close"
                )

            if (
                should_verify
                and self.state.attributes.get(ATTR_DEVICE_CLASS)
                in OpenCloseTrait.COVER_2FA
            ):
                _verify_pin_challenge(data, self.state, challenge)

            await self.hass.services.async_call(
                domain,
                service,
                svc_params,
                blocking=not self.config.should_report_state,
                context=data.context,
            )