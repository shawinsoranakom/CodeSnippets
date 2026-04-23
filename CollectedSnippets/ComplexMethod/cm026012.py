async def _async_handle_event(self, event_message: EventMessage) -> None:
        """Handle a device event."""
        if (
            event_message.relation_update
            or not event_message.resource_update_name
            or not (events := event_message.resource_update_events)
        ):
            return
        last_nest_event_id = self.state_attributes.get("nest_event_id")
        for api_event_type, nest_event in events.items():
            if api_event_type not in self.entity_description.api_event_types:
                continue

            event_type = EVENT_NAME_MAP[api_event_type]
            nest_event_id = nest_event.event_token
            if last_nest_event_id is not None and last_nest_event_id == nest_event_id:
                # This event is a duplicate message in the same thread
                return

            self._trigger_event(
                event_type,
                {"nest_event_id": nest_event_id},
            )
            self.async_write_ha_state()
            return