async def _async_update_data(self) -> dict[str, Any]:
        """Update the data from the Slide device."""
        _LOGGER.debug("Start data update")

        try:
            data = await self.slide.slide_info(self.host)
        except (
            ClientConnectionError,
            AuthenticationFailed,
            ClientTimeoutError,
            DigestAuthCalcError,
        ) as ex:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_error",
            ) from ex

        if data is None:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_error",
            )

        if "pos" in data:
            if self.data is None:
                oldpos = None
            else:
                oldpos = self.data.get("pos")

            data["pos"] = max(0, min(1, data["pos"]))

            if not self.config_entry.options.get(CONF_INVERT_POSITION, False):
                # For slide 0->open, 1->closed; for HA 0->closed, 1->open
                # Value has therefore to be inverted, unless CONF_INVERT_POSITION is true
                data["pos"] = 1 - data["pos"]

            if oldpos is None or oldpos == data["pos"]:
                data["state"] = (
                    STATE_CLOSED if data["pos"] < DEFAULT_OFFSET else STATE_OPEN
                )
            elif oldpos > data["pos"]:
                data["state"] = (
                    STATE_CLOSED if data["pos"] <= DEFAULT_OFFSET else STATE_CLOSING
                )
            else:
                data["state"] = (
                    STATE_OPEN if data["pos"] >= (1 - DEFAULT_OFFSET) else STATE_OPENING
                )

        _LOGGER.debug("Data successfully updated: %s", data)

        return data