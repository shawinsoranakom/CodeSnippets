async def test_save_and_get_conversation_info(
        self,
        service: SQLAppConversationInfoService,
        sample_conversation_info: AppConversationInfo,
    ):
        """Test basic save and get operations."""
        # Save the conversation info
        saved_info = await service.save_app_conversation_info(sample_conversation_info)

        # Verify the saved info matches the original
        assert saved_info.id == sample_conversation_info.id
        assert (
            saved_info.created_by_user_id == sample_conversation_info.created_by_user_id
        )
        assert saved_info.title == sample_conversation_info.title

        # Retrieve the conversation info
        retrieved_info = await service.get_app_conversation_info(
            sample_conversation_info.id
        )

        # Verify the retrieved info matches the original
        assert retrieved_info is not None
        assert retrieved_info.id == sample_conversation_info.id
        assert retrieved_info.sandbox_id == sample_conversation_info.sandbox_id
        assert (
            retrieved_info.selected_repository
            == sample_conversation_info.selected_repository
        )
        assert (
            retrieved_info.selected_branch == sample_conversation_info.selected_branch
        )
        assert retrieved_info.git_provider == sample_conversation_info.git_provider
        assert retrieved_info.title == sample_conversation_info.title
        assert retrieved_info.trigger == sample_conversation_info.trigger
        assert retrieved_info.pr_number == sample_conversation_info.pr_number
        assert retrieved_info.llm_model == sample_conversation_info.llm_model