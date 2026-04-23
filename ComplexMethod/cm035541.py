async def test_round_trip_with_minimal_fields(
        self, service: SQLAppConversationInfoService
    ):
        """Test round trip with only required fields."""
        minimal_info = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='minimal_user',
            sandbox_id='minimal_sandbox',
        )

        # Save and retrieve
        await service.save_app_conversation_info(minimal_info)
        retrieved_info = await service.get_app_conversation_info(minimal_info.id)

        # Verify required fields
        assert retrieved_info is not None
        assert retrieved_info.id == minimal_info.id
        assert retrieved_info.sandbox_id == minimal_info.sandbox_id

        # Verify optional fields are None or default values
        assert retrieved_info.selected_repository is None
        assert retrieved_info.selected_branch is None
        assert retrieved_info.git_provider is None
        assert retrieved_info.title is None
        assert retrieved_info.trigger is None
        assert retrieved_info.pr_number == []
        assert retrieved_info.llm_model is None
        assert retrieved_info.metrics == MetricsSnapshot(
            accumulated_token_usage=TokenUsage()
        )