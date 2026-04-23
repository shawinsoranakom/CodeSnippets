async def post(
        self, request: web.Request, domain: str, service: str
    ) -> web.Response:
        """Call a service.

        Returns a list of changed states.
        """
        hass = request.app[KEY_HASS]
        body = await request.text()
        try:
            data = json_loads(body) if body else None
        except ValueError:
            return self.json_message(
                "Data should be valid JSON.", HTTPStatus.BAD_REQUEST
            )

        context = self.context(request)
        if not hass.services.has_service(domain, service):
            raise HTTPBadRequest from ServiceNotFound(domain, service)

        if response_requested := "return_response" in request.query:
            if (
                hass.services.supports_response(domain, service)
                is ha.SupportsResponse.NONE
            ):
                return self.json_message(
                    "Service does not support responses. Remove return_response from request.",
                    HTTPStatus.BAD_REQUEST,
                )
        elif (
            hass.services.supports_response(domain, service) is ha.SupportsResponse.ONLY
        ):
            return self.json_message(
                "Service call requires responses but caller did not ask for responses. "
                "Add ?return_response to query parameters.",
                HTTPStatus.BAD_REQUEST,
            )

        changed_states: list[json_fragment] = []

        @ha.callback
        def _async_save_changed_entities(
            event: Event[EventStateChangedData],
        ) -> None:
            if event.context == context and (state := event.data["new_state"]):
                changed_states.append(state.json_fragment)

        cancel_listen = hass.bus.async_listen(
            EVENT_STATE_CHANGED,
            _async_save_changed_entities,
        )

        try:
            # shield the service call from cancellation on connection drop
            response = await shield(
                hass.services.async_call(
                    domain,
                    service,
                    data,  # type: ignore[arg-type]
                    blocking=True,
                    context=context,
                    return_response=response_requested,
                )
            )
        except (vol.Invalid, ServiceNotFound) as ex:
            raise HTTPBadRequest from ex
        finally:
            cancel_listen()

        if response_requested:
            return self.json(
                {"changed_states": changed_states, "service_response": response}
            )

        return self.json(changed_states)