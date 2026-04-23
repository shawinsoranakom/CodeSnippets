def augment(self, data: dict[str, Any], context_row: Row | EventAsRow) -> None:
        """Augment data from the row and cache."""
        event_type = context_row[EVENT_TYPE_POS]
        # State change
        if context_entity_id := context_row[ENTITY_ID_POS]:
            data[CONTEXT_STATE] = context_row[STATE_POS]
            data[CONTEXT_ENTITY_ID] = context_entity_id
            if self.include_entity_name:
                data[CONTEXT_ENTITY_ID_NAME] = self.entity_name_cache.get(
                    context_entity_id
                )
            return

        # Call service
        if event_type == EVENT_CALL_SERVICE:
            event = self.event_cache.get(context_row)
            event_data = event.data
            data[CONTEXT_DOMAIN] = event_data.get(ATTR_DOMAIN)
            data[CONTEXT_SERVICE] = event_data.get(ATTR_SERVICE)
            data[CONTEXT_EVENT_TYPE] = event_type
            return

        if event_type not in self.external_events:
            return

        domain, describe_event = self.external_events[event_type]
        data[CONTEXT_EVENT_TYPE] = event_type
        data[CONTEXT_DOMAIN] = domain
        event = self.event_cache.get(context_row)
        try:
            described = describe_event(event)
        except Exception:
            _LOGGER.exception("Error with %s describe event for %s", domain, event_type)
            return
        if name := described.get(LOGBOOK_ENTRY_NAME):
            data[CONTEXT_NAME] = name
        if message := described.get(LOGBOOK_ENTRY_MESSAGE):
            data[CONTEXT_MESSAGE] = message
        # In 2022.12 and later drop `CONTEXT_MESSAGE` if `CONTEXT_SOURCE` is available
        if source := described.get(LOGBOOK_ENTRY_SOURCE):
            data[CONTEXT_SOURCE] = source
        if not (attr_entity_id := described.get(LOGBOOK_ENTRY_ENTITY_ID)):
            return
        data[CONTEXT_ENTITY_ID] = attr_entity_id
        if self.include_entity_name:
            data[CONTEXT_ENTITY_ID_NAME] = self.entity_name_cache.get(attr_entity_id)