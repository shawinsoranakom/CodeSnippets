async def search_events(
        self,
        conversation_id: UUID,
        kind__eq: EventKind | None = None,
        timestamp__gte: datetime | None = None,
        timestamp__lt: datetime | None = None,
        sort_order: EventSortOrder = EventSortOrder.TIMESTAMP,
        page_id: str | None = None,
        limit: int = 100,
    ) -> EventPage:
        """Search events matching the given filters."""
        loop = asyncio.get_running_loop()
        prefix = await self.get_conversation_path(conversation_id)
        paths = await loop.run_in_executor(None, self._search_paths, prefix)

        # Type error: run_in_executor expects a return value, but self._load_event is typed return Event | None.
        events = await asyncio.gather(
            *[loop.run_in_executor(None, self._load_event, path) for path in paths]  # type: ignore[arg-type]
        )
        items = []
        for event in events:
            if not event:
                continue
            if kind__eq and event.kind != kind__eq:
                continue
            # TODO: Are these comparison operators valid?
            if timestamp__gte and event.timestamp < timestamp__gte:  # type: ignore[operator]
                continue
            if timestamp__lt and event.timestamp >= timestamp__lt:  # type: ignore[operator]
                continue
            items.append(event)

        if sort_order:
            items.sort(
                key=lambda e: e.timestamp,
                reverse=(sort_order == EventSortOrder.TIMESTAMP_DESC),
            )

        # Apply pagination to items (not paths)
        start_offset = 0
        next_page_id = None
        if page_id:
            start_offset = int(page_id)
            items = items[start_offset:]
        if len(items) > limit:
            next_page_id = str(start_offset + limit)
            items = items[:limit]

        return EventPage(items=items, next_page_id=next_page_id)