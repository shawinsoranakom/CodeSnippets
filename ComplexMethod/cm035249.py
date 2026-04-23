async def update_conversation_statistics(
        self, conversation_id: UUID, stats: ConversationStats
    ) -> None:
        """Update conversation statistics from stats event data.

        Args:
            conversation_id: The ID of the conversation to update
            stats: ConversationStats object containing usage_to_metrics data from stats event
        """
        # Extract agent metrics from usage_to_metrics
        usage_to_metrics = stats.usage_to_metrics
        agent_metrics = usage_to_metrics.get('agent')

        if not agent_metrics:
            logger.debug(
                'No agent metrics found in stats for conversation %s', conversation_id
            )
            return

        # Query existing record using secure select (filters for V1 and user if available)
        query = await self._secure_select()
        query = query.where(
            StoredConversationMetadata.conversation_id == str(conversation_id)
        )
        result = await self.db_session.execute(query)
        stored = result.scalar_one_or_none()

        if not stored:
            logger.debug(
                'Conversation %s not found or not accessible, skipping statistics update',
                conversation_id,
            )
            return

        # Extract accumulated_cost and max_budget_per_task from Metrics object
        accumulated_cost = agent_metrics.accumulated_cost
        max_budget_per_task = agent_metrics.max_budget_per_task

        # Extract accumulated_token_usage from Metrics object
        accumulated_token_usage = agent_metrics.accumulated_token_usage
        if accumulated_token_usage:
            prompt_tokens = accumulated_token_usage.prompt_tokens
            completion_tokens = accumulated_token_usage.completion_tokens
            cache_read_tokens = accumulated_token_usage.cache_read_tokens
            cache_write_tokens = accumulated_token_usage.cache_write_tokens
            reasoning_tokens = accumulated_token_usage.reasoning_tokens
            context_window = accumulated_token_usage.context_window
            per_turn_token = accumulated_token_usage.per_turn_token
        else:
            prompt_tokens = None
            completion_tokens = None
            cache_read_tokens = None
            cache_write_tokens = None
            reasoning_tokens = None
            context_window = None
            per_turn_token = None

        # Update fields only if values are provided (not None)
        if accumulated_cost is not None:
            stored.accumulated_cost = accumulated_cost
        if max_budget_per_task is not None:
            stored.max_budget_per_task = max_budget_per_task
        if prompt_tokens is not None:
            stored.prompt_tokens = prompt_tokens
        if completion_tokens is not None:
            stored.completion_tokens = completion_tokens
        if cache_read_tokens is not None:
            stored.cache_read_tokens = cache_read_tokens
        if cache_write_tokens is not None:
            stored.cache_write_tokens = cache_write_tokens
        if reasoning_tokens is not None:
            stored.reasoning_tokens = reasoning_tokens
        if context_window is not None:
            stored.context_window = context_window
        if per_turn_token is not None:
            stored.per_turn_token = per_turn_token

        # Update last_updated_at timestamp
        stored.last_updated_at = utc_now()

        await self.db_session.commit()