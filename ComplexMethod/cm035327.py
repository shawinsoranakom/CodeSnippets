def search_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter: EventFilter | None = None,
        limit: int | None = None,
    ) -> Iterable[Event]:
        """Retrieve events from the event stream, optionally filtering out events of a given type
        and events marked as hidden.

        Args:
            start_id: The ID of the first event to retrieve. Defaults to 0.
            end_id: The ID of the last event to retrieve. Defaults to the last event in the stream.
            reverse: Whether to retrieve events in reverse order. Defaults to False.
            filter: EventFilter to use

        Yields:
            Events from the stream that match the criteria.
        """
        if end_id is None:
            end_id = self.cur_id
        else:
            end_id += 1  # From inclusive to exclusive

        if reverse:
            step = -1
            start_id, end_id = end_id, start_id
            start_id -= 1
            end_id -= 1
        else:
            step = 1

        cache_page = _DUMMY_PAGE
        num_results = 0
        for index in range(start_id, end_id, step):
            if not should_continue():
                return
            if not cache_page.covers(index):
                cache_page = self._load_cache_page_for_index(index)
            event = cache_page.get_event(index)
            if event is None:
                try:
                    event = self.get_event(index)
                except FileNotFoundError:
                    event = None
            if event:
                if not filter or filter.include(event):
                    yield event
                    num_results += 1
                    if limit and limit <= num_results:
                        return