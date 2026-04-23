async def search_event_callbacks(
        self,
        conversation_id__eq: UUID | None = None,
        event_kind__eq: EventKind | None = None,
        event_id__eq: UUID | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> EventCallbackPage:
        """Search for event callbacks, optionally filtered by parameters."""
        # Build the query with filters
        conditions = []

        if conversation_id__eq is not None:
            conditions.append(
                StoredEventCallback.conversation_id == conversation_id__eq
            )

        if event_kind__eq is not None:
            conditions.append(StoredEventCallback.event_kind == event_kind__eq)

        # Note: event_id__eq is not stored in the event_callbacks table
        # This parameter might be used for filtering results after retrieval
        # or might be intended for a different use case

        # Build the base query
        stmt = select(StoredEventCallback)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Handle pagination
        if page_id is not None:
            # Parse page_id to get offset or cursor
            try:
                offset = int(page_id)
                stmt = stmt.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        stmt = stmt.limit(limit + 1).order_by(StoredEventCallback.created_at.desc())

        result = await self.db_session.execute(stmt)
        stored_callbacks = result.scalars().all()

        # Check if there are more results
        has_more = len(stored_callbacks) > limit
        if has_more:
            stored_callbacks = stored_callbacks[:limit]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        # Convert stored callbacks to domain models
        callbacks = [
            EventCallback.model_validate(row2dict(cb)) for cb in stored_callbacks
        ]
        return EventCallbackPage(items=callbacks, next_page_id=next_page_id)