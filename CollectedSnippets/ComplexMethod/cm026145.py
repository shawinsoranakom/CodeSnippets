async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if len(self._async_current_entries()) == 5:
            return self.async_abort(reason="max_regions")

        if not self.states:
            websession = async_get_clientsession(self.hass)
            reason = None
            unknown_err_msg = None
            try:
                regions = await Client(websession).get_regions()
            except aiohttp.ClientResponseError as ex:
                if ex.status == 429:
                    reason = "rate_limit"
                else:
                    reason = "unknown"
                    unknown_err_msg = str(ex)
            except aiohttp.ClientConnectionError:
                reason = "cannot_connect"
            except aiohttp.ClientError as ex:
                reason = "unknown"
                unknown_err_msg = str(ex)
            except TimeoutError:
                reason = "timeout"

            if not reason and not regions:
                reason = "unknown"
                unknown_err_msg = "no regions returned"

            if unknown_err_msg:
                _LOGGER.error("Failed to connect to the service: %s", unknown_err_msg)

            if reason:
                return self.async_abort(reason=reason)
            self.states = regions["states"]

        return await self._handle_pick_region("user", "district", user_input)