async def check_connection(
        self, api_token: str
    ) -> tuple[dict[str, str], str | None]:
        """Check connection to the Mealie API."""
        assert self.host is not None

        if "/app/" in self.host:
            return {"base": "ingress_url"}, None

        client = MealieClient(
            self.host,
            token=api_token,
            session=async_get_clientsession(self.hass, verify_ssl=self.verify_ssl),
        )
        try:
            info = await client.get_user_info()
            about = await client.get_about()
            version = create_version(about.version)
        except MealieConnectionError:
            return {"base": "cannot_connect"}, None
        except MealieAuthenticationError:
            return {"base": "invalid_auth"}, None
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected error")
            return {"base": "unknown"}, None
        if version.valid and version < MIN_REQUIRED_MEALIE_VERSION:
            return {"base": "mealie_version"}, None
        return {}, info.user_id