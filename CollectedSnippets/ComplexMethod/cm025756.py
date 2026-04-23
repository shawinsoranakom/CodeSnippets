async def _async_update_data(self) -> dict[str, Any]:
        """Update vehicle data using TeslaFleet API."""

        try:
            # Check if the vehicle is awake using a free API call
            response = await self.api.vehicle()
            self.data["state"] = response["response"]["state"]

            if self.data["state"] != TeslaFleetState.ONLINE:
                return self.data

            response = await self.api.vehicle_data(endpoints=self.endpoints)
            data = response["response"]

        except VehicleOffline:
            self.data["state"] = TeslaFleetState.ASLEEP
            return self.data
        except RateLimited:
            LOGGER.warning(
                "%s rate limited, will skip refresh",
                self.name,
            )
            return self.data
        except (InvalidToken, OAuthExpired) as e:
            _invalidate_access_token(self.hass, self.config_entry)
            raise UpdateFailed(e.message) from e
        except LoginRequired as e:
            raise ConfigEntryAuthFailed from e
        except TeslaFleetError as e:
            raise UpdateFailed(e.message) from e

        self.update_interval = VEHICLE_INTERVAL

        self.updated_once = True

        if self.api.pre2021 and data["state"] == TeslaFleetState.ONLINE:
            # Handle pre-2021 vehicles which cannot sleep by themselves
            if (
                data["charge_state"].get("charging_state") == "Charging"
                or data["vehicle_state"].get("is_user_present")
                or data["vehicle_state"].get("sentry_mode")
            ):
                # Vehicle is active, reset timer
                self.last_active = datetime.now()
            else:
                elapsed = datetime.now() - self.last_active
                if elapsed > timedelta(minutes=20):
                    # Vehicle didn't sleep, try again in 15 minutes
                    self.last_active = datetime.now()
                elif elapsed > timedelta(minutes=15):
                    # Let vehicle go to sleep now
                    self.update_interval = VEHICLE_WAIT

        return flatten(data)