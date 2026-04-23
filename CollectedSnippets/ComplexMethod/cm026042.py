async def _validate_and_create(
        self, step_id: str, data_schema: vol.Schema, data: Mapping[str, Any] | None
    ) -> ConfigFlowResult:
        """Validate data and show form if it is invalid."""
        errors: dict[str, str] = {}

        if data:
            session = async_get_clientsession(self.hass)
            em = ElectricityMaps(token=data[CONF_API_KEY], session=session)

            try:
                await fetch_latest_carbon_intensity(self.hass, em, data)
            except ElectricityMapsInvalidTokenError:
                errors["base"] = "invalid_auth"
            except ElectricityMapsNoDataError:
                errors["base"] = "no_data"
            except Exception:
                _LOGGER.exception("Unexpected error occurred while checking API key")
                errors["base"] = "unknown"
            else:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={CONF_API_KEY: data[CONF_API_KEY]},
                    )

                return self.async_create_entry(
                    title=get_extra_name(data) or "Electricity Maps",
                    data=data,
                )

        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            errors=errors,
            description_placeholders=DESCRIPTION_PLACEHOLDER,
        )