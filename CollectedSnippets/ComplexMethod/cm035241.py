async def search_app_conversation_start_tasks(
        self,
        conversation_id__eq: UUID | None = None,
        created_at__gte: datetime | None = None,
        sort_order: AppConversationStartTaskSortOrder = AppConversationStartTaskSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 100,
    ) -> AppConversationStartTaskPage:
        """Search for conversation start tasks."""
        query = select(StoredAppConversationStartTask)

        # Apply user filter if user_id is set
        if self.user_id:
            query = query.where(
                StoredAppConversationStartTask.created_by_user_id == self.user_id
            )

        # Apply conversation_id filter
        if conversation_id__eq is not None:
            query = query.where(
                StoredAppConversationStartTask.app_conversation_id
                == conversation_id__eq
            )

        # Apply created_at__gte filter
        if created_at__gte is not None:
            query = query.where(
                StoredAppConversationStartTask.created_at >= created_at__gte
            )

        # Add sort order
        if sort_order == AppConversationStartTaskSortOrder.CREATED_AT:
            query = query.order_by(StoredAppConversationStartTask.created_at)
        elif sort_order == AppConversationStartTaskSortOrder.CREATED_AT_DESC:
            query = query.order_by(StoredAppConversationStartTask.created_at.desc())
        elif sort_order == AppConversationStartTaskSortOrder.UPDATED_AT:
            query = query.order_by(StoredAppConversationStartTask.updated_at)
        elif sort_order == AppConversationStartTaskSortOrder.UPDATED_AT_DESC:
            query = query.order_by(StoredAppConversationStartTask.updated_at.desc())

        # Apply pagination
        if page_id is not None:
            try:
                offset = int(page_id)
                query = query.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        rows = result.scalars().all()

        # Check if there are more results
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [AppConversationStartTask.model_validate(row2dict(row)) for row in rows]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        return AppConversationStartTaskPage(items=items, next_page_id=next_page_id)