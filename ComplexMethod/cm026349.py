async def _async_handle_auth_code(
        self,
        hass: HomeAssistant,
        data: MultiDictProxy[str],
        request: web.Request,
    ) -> web.Response:
        """Handle authorization code request."""
        client_id = data.get("client_id")
        if client_id is None or not indieauth.verify_client_id(client_id):
            return self.json(
                {"error": "invalid_request", "error_description": "Invalid client id"},
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if (code := data.get("code")) is None:
            return self.json(
                {"error": "invalid_request", "error_description": "Invalid code"},
                status_code=HTTPStatus.BAD_REQUEST,
            )

        credential = self._retrieve_auth(client_id, code)

        if credential is None or not isinstance(credential, Credentials):
            return self.json(
                {"error": "invalid_request", "error_description": "Invalid code"},
                status_code=HTTPStatus.BAD_REQUEST,
            )

        user = await hass.auth.async_get_or_create_user(credential)

        if user_access_error := async_user_not_allowed_do_auth(hass, user):
            return self.json(
                {
                    "error": "access_denied",
                    "error_description": user_access_error,
                },
                status_code=HTTPStatus.FORBIDDEN,
            )

        refresh_token = await hass.auth.async_create_refresh_token(
            user, client_id, credential=credential
        )
        try:
            access_token = hass.auth.async_create_access_token(
                refresh_token, request.remote
            )
        except InvalidAuthError as exc:
            return self.json(
                {"error": "access_denied", "error_description": str(exc)},
                status_code=HTTPStatus.FORBIDDEN,
            )

        return self.json(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "refresh_token": refresh_token.token,
                "expires_in": int(
                    refresh_token.access_token_expiration.total_seconds()
                ),
                "ha_auth_provider": credential.auth_provider_type,
            },
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
            },
        )