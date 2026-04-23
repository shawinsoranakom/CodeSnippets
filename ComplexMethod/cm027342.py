async def post(self, request: web.Request, entity_id: str) -> web.Response:
        """Update state of entity."""
        user: User = request[KEY_HASS_USER]
        if not user.is_admin:
            raise Unauthorized(entity_id=entity_id)
        hass = request.app[KEY_HASS]

        body = await request.text()

        try:
            data: Any = json_loads(body) if body else None
        except ValueError:
            return self.json_message("Invalid JSON specified.", HTTPStatus.BAD_REQUEST)

        if not isinstance(data, dict):
            return self.json_message(
                "State data should be a JSON object.", HTTPStatus.BAD_REQUEST
            )
        if (new_state := data.get("state")) is None:
            return self.json_message("No state specified.", HTTPStatus.BAD_REQUEST)

        attributes = data.get("attributes")
        force_update = data.get("force_update", False)

        is_new_state = hass.states.get(entity_id) is None

        # Write state
        try:
            hass.states.async_set(
                entity_id, new_state, attributes, force_update, self.context(request)
            )
        except InvalidEntityFormatError:
            return self.json_message(
                "Invalid entity ID specified.", HTTPStatus.BAD_REQUEST
            )
        except InvalidStateError:
            return self.json_message("Invalid state specified.", HTTPStatus.BAD_REQUEST)

        # Read the state back for our response
        status_code = HTTPStatus.CREATED if is_new_state else HTTPStatus.OK
        state = hass.states.get(entity_id)
        assert state
        resp = self.json(state.as_dict(), status_code)

        resp.headers.add("Location", f"/api/states/{entity_id}")

        return resp