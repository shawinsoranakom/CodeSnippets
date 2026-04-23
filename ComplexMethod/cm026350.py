async def _async_handle_refresh_token(
        self,
        hass: HomeAssistant,
        data: MultiDictProxy[str],
        request: web.Request,
    ) -> web.Response:
        """Handle refresh token request."""
        client_id = data.get("client_id")
        if client_id is not None and not indieauth.verify_client_id(client_id):
            return self.json(
                {"error": "invalid_request", "error_description": "Invalid client id"},
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if (token := data.get("refresh_token")) is None:
            return self.json(
                {"error": "invalid_request"}, status_code=HTTPStatus.BAD_REQUEST
            )

        refresh_token = hass.auth.async_get_refresh_token_by_token(token)

        if refresh_token is None:
            return self.json(
                {"error": "invalid_grant"}, status_code=HTTPStatus.BAD_REQUEST
            )

        if refresh_token.client_id != client_id:
            return self.json(
                {"error": "invalid_request"}, status_code=HTTPStatus.BAD_REQUEST
            )

        if user_access_error := async_user_not_allowed_do_auth(
            hass, refresh_token.user
        ):
            return self.json(
                {
                    "error": "access_denied",
                    "error_description": user_access_error,
                },
                status_code=HTTPStatus.FORBIDDEN,
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
                "expires_in": int(
                    refresh_token.access_token_expiration.total_seconds()
                ),
            },
            headers={
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
            },
        )