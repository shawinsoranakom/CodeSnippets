async def _internal_handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> None:
        """Handle webhook callback."""
        if not request.body_exists:
            _LOGGER.debug("Received invalid request from switchbot webhook")
            return

        data = await request.json()
        # Structure validation
        if (
            not isinstance(data, dict)
            or "eventType" not in data
            or data["eventType"] != "changeReport"
            or "eventVersion" not in data
            or data["eventVersion"] != "1"
            or "context" not in data
            or not isinstance(data["context"], dict)
            or "deviceType" not in data["context"]
            or "deviceMac" not in data["context"]
        ):
            _LOGGER.debug("Received invalid data from switchbot webhook %s", repr(data))
            return
        _LOGGER.debug("Received data from switchbot webhook: %s", repr(data))
        deviceMac = data["context"]["deviceMac"]

        if deviceMac not in coordinators_by_id:
            _LOGGER.error(
                "Received data for unknown entity from switchbot webhook: %s", data
            )
            return

        coordinators_by_id[deviceMac].async_set_updated_data(data["context"])