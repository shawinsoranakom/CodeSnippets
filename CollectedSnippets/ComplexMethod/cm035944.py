async def test_successful_callback_execution_issue(
        self,
        mock_saas_gitlab_service_cls,
        mock_get_summary_instruction,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        gitlab_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        conversation_id = uuid4()

        # Common service mocks
        mock_httpx_client = await _setup_happy_path_services(
            mock_get_app_conversation_info_service,
            mock_get_sandbox_service,
            mock_get_httpx_client,
            mock_app_conversation_info,
            mock_sandbox_info,
        )

        mock_get_summary_instruction.return_value = 'Please provide a summary'

        # GitLab service mock
        mock_gitlab_service = AsyncMock()
        mock_saas_gitlab_service_cls.return_value = mock_gitlab_service

        result = await gitlab_callback_processor(
            conversation_id=conversation_id,
            callback=event_callback,
            event=conversation_state_update_event,
        )

        assert result is not None
        assert result.status == EventCallbackResultStatus.SUCCESS
        assert result.event_callback_id == event_callback.id
        assert result.event_id == conversation_state_update_event.id
        assert result.conversation_id == conversation_id
        assert result.detail == 'Test summary from agent'
        assert gitlab_callback_processor.should_request_summary is False

        # Verify GitLab service was called correctly for issue
        mock_saas_gitlab_service_cls.assert_called_once_with(
            external_auth_id='test_keycloak_user'
        )
        mock_gitlab_service.reply_to_issue.assert_called_once_with(
            '12345', '42', 'discussion_123', 'Test summary from agent'
        )
        mock_gitlab_service.reply_to_mr.assert_not_called()

        # Verify httpx call
        mock_httpx_client.post.assert_called_once()
        url_arg, kwargs = mock_httpx_client.post.call_args
        url = url_arg[0] if url_arg else kwargs['url']
        assert 'ask_agent' in url
        assert kwargs['headers']['X-Session-API-Key'] == 'test_api_key'
        assert kwargs['json']['question'] == 'Please provide a summary'