async def test_parent_conversation_id_preserved_with_other_metadata(
        self,
        async_session,
        app_conversation_info_service,
        sandbox_info,
        mock_conversation_info,
    ):
        """Test that parent_conversation_id is preserved alongside other metadata.

        Arrange:
            - Create existing conversation with parent and multiple metadata fields
        Act:
            - Call on_conversation_update webhook
        Assert:
            - All metadata including parent_conversation_id is preserved
        """

        # Arrange
        parent_id = uuid4()
        conversation_id = mock_conversation_info.id

        # Create existing conversation with comprehensive metadata
        existing_conv = AppConversationInfo(
            id=conversation_id,
            title='Full Metadata Conversation',
            sandbox_id='sandbox_123',
            created_by_user_id='user_123',
            selected_repository='https://github.com/test/repo',
            selected_branch='feature-branch',
            git_provider=ProviderType.GITHUB,
            trigger=ConversationTrigger.RESOLVER,
            pr_number=[123, 456],
            parent_conversation_id=parent_id,
        )

        # Act - call on_conversation_update directly with mocked valid_conversation
        with patch(
            'openhands.app_server.event_callback.webhook_router.valid_conversation',
            return_value=existing_conv,
        ):
            result = await on_conversation_update(
                conversation_info=mock_conversation_info,
                sandbox_info=sandbox_info,
                app_conversation_info_service=app_conversation_info_service,
            )

        # Assert
        assert isinstance(result, Success)

        saved_conv = await app_conversation_info_service.get_app_conversation_info(
            conversation_id
        )
        assert saved_conv is not None

        # Verify parent_conversation_id is preserved
        assert saved_conv.parent_conversation_id == parent_id

        # Verify other metadata is also preserved
        assert saved_conv.selected_repository == 'https://github.com/test/repo'
        assert saved_conv.selected_branch == 'feature-branch'
        assert saved_conv.git_provider == ProviderType.GITHUB
        assert saved_conv.trigger == ConversationTrigger.RESOLVER
        assert saved_conv.pr_number == [123, 456]