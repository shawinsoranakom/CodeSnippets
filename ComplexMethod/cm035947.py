async def test_successful_callback_execution(
        self,
        mock_github,
        mock_github_integration,
        mock_auth,
        mock_get_summary_instruction,
        mock_get_httpx_client,
        mock_get_sandbox_service,
        mock_get_app_conversation_info_service,
        github_callback_processor,
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

        # Auth.AppAuth and Auth.Token mock
        mock_app_auth_instance = MagicMock()
        mock_auth.AppAuth.return_value = mock_app_auth_instance
        mock_token_auth_instance = MagicMock()
        mock_auth.Token.return_value = mock_token_auth_instance

        # GitHub integration
        mock_token_data = MagicMock()
        mock_token_data.token = 'test_access_token'
        mock_integration_instance = MagicMock()
        mock_integration_instance.get_access_token.return_value = mock_token_data
        mock_github_integration.return_value = mock_integration_instance

        # GitHub API
        mock_github_client = MagicMock()
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value.__enter__.return_value = mock_github_client

        result = await github_callback_processor(
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
        assert github_callback_processor.should_request_summary is False

        mock_auth.AppAuth.assert_called_once_with('test_client_id', 'test_private_key')
        mock_github_integration.assert_called_once_with(auth=mock_app_auth_instance)
        mock_integration_instance.get_access_token.assert_called_once_with(12345)

        mock_auth.Token.assert_called_once_with('test_access_token')
        mock_github.assert_called_once_with(auth=mock_token_auth_instance)
        mock_github_client.get_repo.assert_called_once_with('test-owner/test-repo')
        mock_repo.get_issue.assert_called_once_with(number=42)
        mock_issue.create_comment.assert_called_once_with('Test summary from agent')

        mock_httpx_client.post.assert_called_once()
        url_arg, kwargs = mock_httpx_client.post.call_args
        url = url_arg[0] if url_arg else kwargs['url']
        assert 'ask_agent' in url
        assert kwargs['headers']['X-Session-API-Key'] == 'test_api_key'
        assert kwargs['json']['question'] == 'Please provide a summary'