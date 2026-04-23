async def test_round_trip_with_all_fields(
        self, service: SQLAppConversationInfoService
    ):
        """Test round trip with all possible fields populated."""
        original_info = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_456',
            sandbox_id='sandbox_full_test',
            selected_repository='https://github.com/full/test',
            selected_branch='feature/test',
            git_provider=ProviderType.GITLAB,
            title='Full Test Conversation',
            trigger=ConversationTrigger.RESOLVER,
            pr_number=[789, 101112],
            llm_model='claude-3',
            metrics=MetricsSnapshot(accumulated_token_usage=TokenUsage()),
            created_at=datetime(2024, 2, 15, 10, 30, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 2, 15, 11, 45, 0, tzinfo=timezone.utc),
        )

        # Save and retrieve
        await service.save_app_conversation_info(original_info)
        retrieved_info = await service.get_app_conversation_info(original_info.id)

        # Verify all fields
        assert retrieved_info is not None
        assert retrieved_info.id == original_info.id
        assert retrieved_info.sandbox_id == original_info.sandbox_id
        assert retrieved_info.selected_repository == original_info.selected_repository
        assert retrieved_info.selected_branch == original_info.selected_branch
        assert retrieved_info.git_provider == original_info.git_provider
        assert retrieved_info.title == original_info.title
        assert retrieved_info.trigger == original_info.trigger
        assert retrieved_info.pr_number == original_info.pr_number
        assert retrieved_info.llm_model == original_info.llm_model
        assert retrieved_info.metrics == original_info.metrics