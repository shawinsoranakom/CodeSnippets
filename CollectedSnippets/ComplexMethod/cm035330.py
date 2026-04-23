def include(self, event: Event) -> bool:
        """Determine if an event should be included based on the filter criteria.

        This method checks if the given event matches all the filter criteria.
        If any criterion fails, the event is excluded.

        Args:
            event: The Event object to check against the filter criteria.

        Returns:
            bool: True if the event passes all filter criteria and should be included,
                  False otherwise.
        """
        if self.include_types and not isinstance(event, self.include_types):
            return False

        if self.exclude_types is not None and isinstance(event, self.exclude_types):
            return False

        if self.source:
            if event.source is None or event.source.value != self.source:
                return False

        if (
            self.start_date
            and event.timestamp is not None
            and event.timestamp < self.start_date
        ):
            return False

        if (
            self.end_date
            and event.timestamp is not None
            and event.timestamp > self.end_date
        ):
            return False

        if self.exclude_hidden and getattr(event, 'hidden', False):
            return False

        # Text search in event content if query provided
        if self.query:
            event_dict = event_to_dict(event)
            event_str = json.dumps(event_dict).lower()
            if self.query.lower() not in event_str:
                return False

        return True