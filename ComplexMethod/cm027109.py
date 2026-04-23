def _event_listener(event: Event) -> None:
            """Listen for new events and put them in the process queue."""
            if event.event_type in exclude_event_types:
                return

            if entity_filter is None or not (
                entity_id := event.data.get(ATTR_ENTITY_ID)
            ):
                queue_put(event)
                return

            if isinstance(entity_id, str):
                if entity_filter(entity_id):
                    queue_put(event)
                return

            if isinstance(entity_id, list):
                for eid in entity_id:
                    if entity_filter(eid):
                        queue_put(event)
                        return
                return

            # Unknown what it is.
            queue_put(event)