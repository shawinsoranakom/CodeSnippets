async def test_update_statistics_success(
        self, service, async_session, v1_conversation_metadata
    ):
        """Test successfully updating conversation statistics."""
        conversation_id, stored = v1_conversation_metadata

        agent_metrics = Metrics(
            model_name='test-model',
            accumulated_cost=0.03411525,
            max_budget_per_task=10.0,
            accumulated_token_usage=TokenUsage(
                model='test-model',
                prompt_tokens=8770,
                completion_tokens=82,
                cache_read_tokens=0,
                cache_write_tokens=8767,
                reasoning_tokens=0,
                context_window=0,
                per_turn_token=8852,
            ),
        )
        stats = ConversationStats(usage_to_metrics={'agent': agent_metrics})

        await service.update_conversation_statistics(conversation_id, stats)

        # Verify the update
        await async_session.refresh(stored)
        assert stored.accumulated_cost == 0.03411525
        assert stored.max_budget_per_task == 10.0
        assert stored.prompt_tokens == 8770
        assert stored.completion_tokens == 82
        assert stored.cache_read_tokens == 0
        assert stored.cache_write_tokens == 8767
        assert stored.reasoning_tokens == 0
        assert stored.context_window == 0
        assert stored.per_turn_token == 8852
        assert stored.last_updated_at is not None