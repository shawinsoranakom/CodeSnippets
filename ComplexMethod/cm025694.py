async def async_webhook_handler(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> Response | None:
        if not request.body_exists:
            return HomeAssistantView.json(
                result="No Body", status_code=HTTPStatus.BAD_REQUEST
            )

        body = await request.json()

        _LOGGER.debug("Received webhook: %s", body)

        data = WebhookEvent.parse_webhook_event(body)

        body_type = body.get("type")

        if not (coordinator_data := coordinator.data):
            pass
        elif body_type == WEBHOOK_VALVE_TYPE:
            coordinator_data.state.valve_state = data.state
        elif body_type == WEBHOOK_TELEMETRY_TYPE:
            errors = data.errors or {}
            coordinator_data.telemetry.flow = (
                data.flow if "flow" not in errors else None
            )
            coordinator_data.telemetry.pressure = (
                data.pressure if "pressure" not in errors else None
            )
            coordinator_data.telemetry.water_temperature = (
                data.temperature if "temperature" not in errors else None
            )
        elif body_type == WEBHOOK_WIFI_CHANGED_TYPE:
            coordinator_data.networking.ip = data.ip
            coordinator_data.networking.gateway = data.gateway
            coordinator_data.networking.subnet = data.subnet
            coordinator_data.networking.ssid = data.ssid
            coordinator_data.networking.rssi = data.rssi
        elif body_type == WEBHOOK_POWER_SUPPLY_CHANGED_TYPE:
            coordinator_data.state.power_supply = data.supply
        elif body_type == WEBHOOK_AUTO_SHUT_OFF:
            async_dispatcher_send(
                hass, AUTO_SHUT_OFF_EVENT_NAME.format(data.type.lower()), data
            )

        coordinator.async_set_updated_data(coordinator_data)

        return HomeAssistantView.json(result="OK", status_code=HTTPStatus.OK)