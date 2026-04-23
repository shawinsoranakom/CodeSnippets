def _to_info(
        self,
        stored: StoredConversationMetadata,
        sub_conversation_ids: list[UUID] | None = None,
    ) -> AppConversationInfo:
        # V1 conversations should always have a sandbox_id
        sandbox_id = stored.sandbox_id
        assert sandbox_id is not None

        # Rebuild token usage (use 0 as default for nullable int columns)
        token_usage = TokenUsage(
            prompt_tokens=stored.prompt_tokens or 0,
            completion_tokens=stored.completion_tokens or 0,
            cache_read_tokens=stored.cache_read_tokens or 0,
            cache_write_tokens=stored.cache_write_tokens or 0,
            context_window=stored.context_window or 0,
            per_turn_token=stored.per_turn_token or 0,
        )

        # Rebuild metrics object (use 0.0 as default for nullable float columns)
        metrics = MetricsSnapshot(
            accumulated_cost=stored.accumulated_cost or 0.0,
            max_budget_per_task=stored.max_budget_per_task,
            accumulated_token_usage=token_usage,
        )

        # Get timestamps
        created_at = self._fix_timezone(stored.created_at)
        updated_at = self._fix_timezone(stored.last_updated_at)

        return AppConversationInfo(
            id=UUID(stored.conversation_id),
            created_by_user_id=None,  # User ID is now stored in ConversationMetadataSaas
            sandbox_id=sandbox_id,  # Use the asserted non-None value
            selected_repository=stored.selected_repository,
            selected_branch=stored.selected_branch,
            git_provider=(
                ProviderType(stored.git_provider) if stored.git_provider else None
            ),
            title=stored.title,
            trigger=ConversationTrigger(stored.trigger) if stored.trigger else None,
            pr_number=stored.pr_number or [],
            llm_model=stored.llm_model,
            metrics=metrics,
            parent_conversation_id=(
                UUID(stored.parent_conversation_id)
                if stored.parent_conversation_id
                else None
            ),
            sub_conversation_ids=sub_conversation_ids or [],
            public=stored.public,
            tags=stored.tags or {},
            created_at=created_at,
            updated_at=updated_at,
        )