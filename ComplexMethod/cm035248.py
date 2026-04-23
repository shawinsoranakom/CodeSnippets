async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        metrics = info.metrics or MetricsSnapshot()
        usage = metrics.accumulated_token_usage or TokenUsage()

        stored = StoredConversationMetadata(
            conversation_id=str(info.id),
            selected_repository=info.selected_repository,
            selected_branch=info.selected_branch,
            git_provider=info.git_provider.value if info.git_provider else None,
            title=info.title,
            last_updated_at=info.updated_at,
            created_at=info.created_at,
            trigger=info.trigger.value if info.trigger else None,
            pr_number=info.pr_number or [],
            # Cost and token metrics
            accumulated_cost=metrics.accumulated_cost,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=0,
            max_budget_per_task=metrics.max_budget_per_task,
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            context_window=usage.context_window,
            per_turn_token=usage.per_turn_token,
            llm_model=info.llm_model,
            conversation_version='V1',
            sandbox_id=info.sandbox_id,
            parent_conversation_id=(
                str(info.parent_conversation_id)
                if info.parent_conversation_id
                else None
            ),
            public=info.public,
            tags=info.tags if info.tags else None,
        )

        await self.db_session.merge(stored)
        await self.db_session.commit()
        return info