async def get(self, request: web.Request) -> web.Response:
        """Get available auth providers."""
        hass = request.app[KEY_HASS]
        if not onboarding.async_is_user_onboarded(hass):
            return self.json_message(
                message="Onboarding not finished",
                status_code=HTTPStatus.BAD_REQUEST,
                message_code="onboarding_required",
            )

        try:
            remote_address = ip_address(request.remote)  # type: ignore[arg-type]
        except ValueError:
            return self.json_message(
                message="Invalid remote IP",
                status_code=HTTPStatus.BAD_REQUEST,
                message_code="invalid_remote_ip",
            )

        cloud_connection = is_cloud_connection(hass)

        providers = []
        for provider in hass.auth.auth_providers:
            if provider.type == "trusted_networks":
                if cloud_connection:
                    # Skip quickly as trusted networks are not available on cloud
                    continue

                try:
                    cast("TrustedNetworksAuthProvider", provider).async_validate_access(
                        remote_address
                    )
                except InvalidAuthError:
                    # Not a trusted network, so we don't expose that trusted_network authenticator is setup
                    continue

            providers.append(
                {
                    "name": provider.name,
                    "id": provider.id,
                    "type": provider.type,
                }
            )

        preselect_remember_me = not cloud_connection and is_local(remote_address)

        return self.json(
            {
                "providers": providers,
                "preselect_remember_me": preselect_remember_me,
            }
        )