async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._api_token = api_token = user_input[CONF_API_TOKEN]
            client = Elvia(meter_value_token=api_token).meter_value()
            try:
                end_time = dt_util.utcnow()
                results = await client.get_meter_values(
                    start_time=(end_time - timedelta(hours=1)).isoformat(),
                    end_time=end_time.isoformat(),
                )

            except ElviaError.AuthError as exception:
                LOGGER.error("Authentication error %s", exception)
                errors["base"] = "invalid_auth"
            except ElviaError.ElviaException as exception:
                LOGGER.error("Unknown error %s", exception)
                errors["base"] = "unknown"
            else:
                try:
                    self._metering_point_ids = metering_point_ids = [
                        x["meteringPointId"] for x in results["meteringpoints"]
                    ]
                except KeyError:
                    return self.async_abort(reason="no_metering_points")

                if (meter_count := len(metering_point_ids)) > 1:
                    return await self.async_step_select_meter()
                if meter_count == 1:
                    return await self._create_config_entry(
                        api_token=api_token,
                        metering_point_id=metering_point_ids[0],
                    )

                return self.async_abort(reason="no_metering_points")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_TOKEN): str,
                }
            ),
            errors=errors,
        )