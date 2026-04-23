async def _async_update_data(self) -> dict[str, Any]:
        """Update energy history data using Tessie API."""

        try:
            data = (await self.api.energy_history(TeslaEnergyPeriod.DAY))["response"]
        except (InvalidToken, MissingToken) as e:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from e
        except TeslaFleetError as e:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from e

        if (
            not data
            or not isinstance(data.get("time_series"), list)
            or not data["time_series"]
        ):
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_energy_history_data",
            )

        time_series = data["time_series"]
        output: dict[str, Any] = {}
        for key in ENERGY_HISTORY_FIELDS:
            values = [p[key] for p in time_series if key in p]
            output[key] = sum(values) if values else None

        output["_period_start"] = dt_util.parse_datetime(time_series[0]["timestamp"])

        return output