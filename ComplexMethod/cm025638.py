def _event_filter(self, event: Event) -> bool:
        """Return True if the event is visible and not declined."""

        if any(
            attendee.is_self and attendee.response_status == ResponseStatus.DECLINED
            for attendee in event.attendees
        ):
            return False
        # Calendar enttiy may be limited to a specific event type
        if (
            self.entity_description.event_type is not None
            and self.entity_description.event_type != event.event_type
        ):
            return False
        # Default calendar entity omits the special types but includes all the others
        if (
            self.entity_description.event_type is None
            and event.event_type in FILTERED_EVENT_TYPES
        ):
            return False
        if self._ignore_availability:
            return True
        return event.transparency == OPAQUE