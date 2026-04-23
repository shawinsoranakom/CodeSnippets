async def _handle_insights_add(self, msg: WebsocketMessage) -> None:
        """Handle access insights events (entry/exit)."""
        insights = cast(InsightsAdd, msg)
        door_entries = insights.data.metadata.door
        if not door_entries:
            return
        event_type = (
            "access_granted" if insights.data.result == "ACCESS" else "access_denied"
        )
        attrs: dict[str, Any] = {}
        if insights.data.metadata.actor.display_name:
            attrs["actor"] = insights.data.metadata.actor.display_name
        if insights.data.metadata.authentication.display_name:
            attrs["authentication"] = insights.data.metadata.authentication.display_name
        if insights.data.result:
            attrs["result"] = insights.data.result
        for door in door_entries:
            if door.id:
                self._dispatch_door_event(door.id, "access", event_type, attrs)