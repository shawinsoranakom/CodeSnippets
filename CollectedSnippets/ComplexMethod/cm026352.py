async def _async_flow_result_to_response(
        self,
        request: web.Request,
        client_id: str,
        result: AuthFlowResult,
    ) -> web.Response:
        """Convert the flow result to a response."""
        if result["type"] != data_entry_flow.FlowResultType.CREATE_ENTRY:
            # @log_invalid_auth does not work here since it returns HTTP 200.
            # We need to manually log failed login attempts.
            if (
                result["type"] == data_entry_flow.FlowResultType.FORM
                and (errors := result.get("errors"))
                and errors.get("base")
                in (
                    "invalid_auth",
                    "invalid_code",
                )
            ):
                await process_wrong_login(request)
            return self.json(_prepare_result_json(result))

        hass = request.app[KEY_HASS]

        if not await indieauth.verify_redirect_uri(
            hass, client_id, result["context"]["redirect_uri"]
        ):
            return self.json_message("Invalid redirect URI", HTTPStatus.FORBIDDEN)

        result.pop("data")
        result.pop("context")

        result_obj = result.pop("result")

        # Result can be None if credential was never linked to a user before.
        user = await hass.auth.async_get_user_by_credentials(result_obj)

        if user is not None and (
            user_access_error := async_user_not_allowed_do_auth(hass, user)
        ):
            return self.json_message(
                f"Login blocked: {user_access_error}", HTTPStatus.FORBIDDEN
            )

        process_success_login(request)
        # We overwrite the Credentials object with the string code to retrieve it.
        result["result"] = self._store_result(client_id, result_obj)  # type: ignore[typeddict-item]

        return self.json(result)