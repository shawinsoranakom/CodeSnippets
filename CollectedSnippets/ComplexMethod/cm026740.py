async def _execute_cover_or_valve(self, command, data, params, challenge):
        """Execute a StartStop command."""
        domain = self.state.domain
        if command == COMMAND_START_STOP:
            assumed_state_or_set_position = bool(
                (
                    self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
                    & COVER_VALVE_SET_POSITION_FEATURE[domain]
                )
                or self.state.attributes.get(ATTR_ASSUMED_STATE)
            )

            if params["start"] is False:
                if (
                    self.state.state
                    in (
                        COVER_VALVE_STATES[domain]["closing"],
                        COVER_VALVE_STATES[domain]["opening"],
                    )
                    or assumed_state_or_set_position
                ):
                    await self.hass.services.async_call(
                        domain,
                        SERVICE_STOP_COVER_VALVE[domain],
                        {ATTR_ENTITY_ID: self.state.entity_id},
                        blocking=not self.config.should_report_state,
                        context=data.context,
                    )
                else:
                    raise SmartHomeError(
                        ERR_ALREADY_STOPPED,
                        f"{FRIENDLY_DOMAIN[domain]} is already stopped",
                    )
            elif (
                self.state.state
                in (
                    COVER_VALVE_STATES[domain]["open"],
                    COVER_VALVE_STATES[domain]["closed"],
                )
                or assumed_state_or_set_position
            ):
                await self.hass.services.async_call(
                    domain,
                    SERVICE_TOGGLE_COVER_VALVE[domain],
                    {ATTR_ENTITY_ID: self.state.entity_id},
                    blocking=not self.config.should_report_state,
                    context=data.context,
                )
        else:
            raise SmartHomeError(
                ERR_NOT_SUPPORTED, f"Command {command} is not supported"
            )