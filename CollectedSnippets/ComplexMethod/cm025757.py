async def _async_update_data(self) -> dict[str, Any]:
        """Update energy site data using TeslaFleet API."""

        self.update_interval = ENERGY_INTERVAL

        try:
            data = (await self.api.live_status())["response"]
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

        if not isinstance(data, dict):
            LOGGER.debug(
                "%s got unexpected live status response type: %s",
                self.name,
                type(data).__name__,
            )
            return self.data

        # Convert Wall Connectors from array to dict
        wall_connectors = data.get("wall_connectors")
        if not isinstance(wall_connectors, list):
            wall_connectors = []
        data["wall_connectors"] = {
            wc["din"]: wc
            for wc in wall_connectors
            if isinstance(wc, dict) and "din" in wc
        }

        self.updated_once = True
        return data