async def _async_update_data(self) -> dict[str, Any]:
        """Update energy site history data using Tesla Fleet API."""

        try:
            data = (await self.api.energy_history(TeslaEnergyPeriod.DAY))["response"]
        except RateLimited as e:
            if isinstance(e.data, dict) and "after" in e.data:
                LOGGER.warning(
                    "%s rate limited, will retry in %s seconds",
                    self.name,
                    e.data["after"],
                )
                self.update_interval = timedelta(seconds=int(e.data["after"]))
            else:
                LOGGER.warning("%s rate limited, will skip refresh", self.name)
            return self.data
        except (InvalidToken, OAuthExpired) as e:
            _invalidate_access_token(self.hass, self.config_entry)
            raise UpdateFailed(e.message) from e
        except LoginRequired as e:
            raise ConfigEntryAuthFailed from e
        except TeslaFleetError as e:
            raise UpdateFailed(e.message) from e
        self.updated_once = True

        if (
            not data
            or not isinstance((time_series := data.get("time_series")), list)
            or not time_series
            or not isinstance((first_period := time_series[0]), dict)
            or not isinstance((timestamp := first_period.get("timestamp")), str)
            or (period_start := dt_util.parse_datetime(timestamp)) is None
        ):
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_data",
            )

        # Add all time periods together
        output: dict[str, Any] = dict.fromkeys(ENERGY_HISTORY_FIELDS, None)
        for period in time_series:
            for key in ENERGY_HISTORY_FIELDS:
                if key in period:
                    if output[key] is None:
                        output[key] = period[key]
                    else:
                        output[key] += period[key]

        output["_period_start"] = period_start

        return output