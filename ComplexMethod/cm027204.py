async def _handle_logs_add(self, msg: WebsocketMessage) -> None:
        """Handle access log events (entry/exit via access.logs.add)."""
        log = cast(LogAdd, msg)
        source = log.data.source
        device_target = source.device_config
        if device_target is None:
            return
        if device_target.id in self._device_to_door:
            door_id = self._device_to_door[device_target.id]
        elif msg.door_id:
            # UAH-DOOR devices: door_id is enriched by the library via MAC→door map
            door_id = msg.door_id
        else:
            return
        event_type = (
            "access_granted" if source.event.result == "ACCESS" else "access_denied"
        )
        attrs: dict[str, Any] = {}
        if source.actor.display_name:
            attrs["actor"] = source.actor.display_name
        if source.authentication.credential_provider:
            attrs["authentication"] = source.authentication.credential_provider
        if source.event.result:
            attrs["result"] = source.event.result
        self._dispatch_door_event(door_id, "access", event_type, attrs)