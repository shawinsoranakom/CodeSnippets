async def _async_update_data(self) -> dict[str, Any]:
        """Update energy site data using Teslemetry API."""
        try:
            data = (await self.api.energy_history(TeslaEnergyPeriod.DAY))["response"]
        except (InvalidToken, SubscriptionRequired, LoginRequired) as e:
            raise ConfigEntryAuthFailed from e
        except RETRY_EXCEPTIONS as e:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                retry_after=_get_retry_after(e),
            ) from e
        except TeslaFleetError as e:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
            ) from e

        if not data or not isinstance(data.get("time_series"), list):
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed_invalid_data",
            )

        # Add all time periods together
        output = dict.fromkeys(ENERGY_HISTORY_FIELDS, None)
        for period in data.get("time_series", []):
            for key in ENERGY_HISTORY_FIELDS:
                if key in period:
                    if output[key] is None:
                        output[key] = period[key]
                    else:
                        output[key] += period[key]

        return output