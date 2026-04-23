async def search_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        sandbox_id__eq: str | None = None,
        sort_order: AppConversationSortOrder = AppConversationSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 100,
        include_sub_conversations: bool = False,
    ) -> AppConversationInfoPage:
        """Search for conversations with user_id from SAAS metadata."""
        query = await self._secure_select_with_saas_metadata()

        # Conditionally exclude sub-conversations based on the parameter
        if not include_sub_conversations:
            # Exclude sub-conversations (only include top-level conversations)
            query = query.where(
                StoredConversationMetadata.parent_conversation_id.is_(None)
            )

        query = self._apply_filters_with_saas_metadata(
            query=query,
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
            sandbox_id__eq=sandbox_id__eq,
        )

        # Add sort order
        if sort_order == AppConversationSortOrder.CREATED_AT:
            query = query.order_by(StoredConversationMetadata.created_at)
        elif sort_order == AppConversationSortOrder.CREATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.created_at.desc())
        elif sort_order == AppConversationSortOrder.UPDATED_AT:
            query = query.order_by(StoredConversationMetadata.last_updated_at)
        elif sort_order == AppConversationSortOrder.UPDATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.last_updated_at.desc())
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(StoredConversationMetadata.title)
        elif sort_order == AppConversationSortOrder.TITLE_DESC:
            query = query.order_by(StoredConversationMetadata.title.desc())

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

        result = await self.db_session.execute(query)
        rows = result.all()

        # Check if there are more results
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            self._to_info_with_user_id(stored_metadata, saas_metadata)
            for stored_metadata, saas_metadata in rows
        ]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        return AppConversationInfoPage(items=items, next_page_id=next_page_id)