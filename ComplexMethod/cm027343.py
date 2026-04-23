async def post(self, request: web.Request, event_type: str) -> web.Response:
        """Fire events."""
        body = await request.text()
        try:
            event_data: Any = json_loads(body) if body else None
        except ValueError:
            return self.json_message(
                "Event data should be valid JSON.", HTTPStatus.BAD_REQUEST
            )

        if event_data is not None and not isinstance(event_data, dict):
            return self.json_message(
                "Event data should be a JSON object", HTTPStatus.BAD_REQUEST
            )

        # Special case handling for event STATE_CHANGED
        # We will try to convert state dicts back to State objects
        if event_type == EVENT_STATE_CHANGED and event_data:
            for key in ("old_state", "new_state"):
                state = ha.State.from_dict(event_data[key])

                if state:
                    event_data[key] = state

        request.app[KEY_HASS].bus.async_fire(
            event_type, event_data, ha.EventOrigin.remote, self.context(request)
        )

        return self.json_message(f"Event {event_type} fired.")