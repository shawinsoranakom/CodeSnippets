async def async_call_service(
        self, domain: str, service: str, intent_obj: intent.Intent, state: State
    ) -> None:
        """Call service on entity with handling for special cases."""
        hass = intent_obj.hass

        if state.domain in (BUTTON_DOMAIN, INPUT_BUTTON_DOMAIN):
            if service != SERVICE_TURN_ON:
                raise intent.IntentHandleError(
                    f"Entity {state.entity_id} cannot be turned off"
                )

            await self._run_then_background(
                hass.async_create_task(
                    hass.services.async_call(
                        state.domain,
                        SERVICE_PRESS_BUTTON,
                        {ATTR_ENTITY_ID: state.entity_id},
                        context=intent_obj.context,
                        blocking=True,
                    )
                )
            )
            return

        if state.domain == COVER_DOMAIN:
            # on = open
            # off = close
            if service == SERVICE_TURN_ON:
                service_name = SERVICE_OPEN_COVER
            else:
                service_name = SERVICE_CLOSE_COVER

            await self._run_then_background(
                hass.async_create_task(
                    hass.services.async_call(
                        COVER_DOMAIN,
                        service_name,
                        {ATTR_ENTITY_ID: state.entity_id},
                        context=intent_obj.context,
                        blocking=True,
                    )
                )
            )
            return

        if state.domain == LOCK_DOMAIN:
            # on = lock
            # off = unlock
            if service == SERVICE_TURN_ON:
                service_name = SERVICE_LOCK
            else:
                service_name = SERVICE_UNLOCK

            await self._run_then_background(
                hass.async_create_task(
                    hass.services.async_call(
                        LOCK_DOMAIN,
                        service_name,
                        {ATTR_ENTITY_ID: state.entity_id},
                        context=intent_obj.context,
                        blocking=True,
                    )
                )
            )
            return

        if state.domain == VALVE_DOMAIN:
            # on = opened
            # off = closed
            if service == SERVICE_TURN_ON:
                service_name = SERVICE_OPEN_VALVE
            else:
                service_name = SERVICE_CLOSE_VALVE

            await self._run_then_background(
                hass.async_create_task(
                    hass.services.async_call(
                        VALVE_DOMAIN,
                        service_name,
                        {ATTR_ENTITY_ID: state.entity_id},
                        context=intent_obj.context,
                        blocking=True,
                    )
                )
            )
            return

        if not hass.services.has_service(state.domain, service):
            raise intent.IntentHandleError(
                f"Service {service} does not support entity {state.entity_id}"
            )

        # Fall back to homeassistant.turn_on/off
        await super().async_call_service(domain, service, intent_obj, state)