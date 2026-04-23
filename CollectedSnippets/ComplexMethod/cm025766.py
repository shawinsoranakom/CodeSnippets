async def async_oauth_create_entry(
        self,
        data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle OAuth completion and proceed to domain registration."""
        token = jwt.decode(
            data["token"]["access_token"], options={"verify_signature": False}
        )

        self.data = data
        self.uid = token["sub"]

        await self.async_set_unique_id(self.uid)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data=data
            )
        self._abort_if_unique_id_configured()

        # OAuth done, setup Partner API connections for all regions
        implementation = cast(TeslaUserImplementation, self.flow_impl)
        session = async_get_clientsession(self.hass)
        failed_regions: list[str] = []

        for region, server_url in SERVERS.items():
            if region == "cn":
                continue
            api = TeslaFleetApi(
                session=session,
                access_token="",
                server=server_url,
                partner_scope=True,
                charging_scope=False,
                energy_scope=False,
                user_scope=False,
                vehicle_scope=False,
            )
            await api.get_private_key(self.hass.config.path("tesla_fleet.key"))
            try:
                await api.partner_login(
                    implementation.client_id,
                    implementation.client_secret,
                    [Scope.OPENID],
                )
            except (InvalidToken, OAuthExpired, LoginRequired) as err:
                LOGGER.warning(
                    "Partner login failed for %s due to an authentication error: %s",
                    server_url,
                    err,
                )
                return self.async_abort(reason="oauth_error")
            except TeslaFleetError as err:
                LOGGER.warning("Partner login failed for %s: %s", server_url, err)
                failed_regions.append(server_url)
                continue
            self.apis.append(api)

        if not self.apis:
            LOGGER.warning(
                "Partner login failed for all regions: %s", ", ".join(failed_regions)
            )
            return self.async_abort(reason="oauth_error")

        if failed_regions:
            LOGGER.warning(
                "Partner login succeeded on some regions but failed on: %s",
                ", ".join(failed_regions),
            )

        return await self.async_step_domain_input()