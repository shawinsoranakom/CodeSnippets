async def _validate_input(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, str], UptimeRobotAccount | None]:
        """Validate the user input allows us to connect."""
        errors: dict[str, str] = {}
        response: UptimeRobotApiResponse | None = None
        key: str = data[CONF_API_KEY]
        if key.startswith(("ur", "m")):
            LOGGER.error("Wrong API key type detected, use the 'main' API key")
            errors["base"] = "not_main_key"
            return errors, None
        uptime_robot_api = UptimeRobot(key, async_get_clientsession(self.hass))

        try:
            response = await uptime_robot_api.async_get_account_details()
        except UptimeRobotAuthenticationException:
            errors["base"] = "invalid_api_key"
        except UptimeRobotException:
            errors["base"] = "cannot_connect"
        except Exception as exception:  # noqa: BLE001
            LOGGER.exception(exception)
            errors["base"] = "unknown"

        if TYPE_CHECKING:
            assert response is not None
            assert isinstance(response.data, UptimeRobotAccount)

        account: UptimeRobotAccount | None = response.data if response else None

        return errors, account