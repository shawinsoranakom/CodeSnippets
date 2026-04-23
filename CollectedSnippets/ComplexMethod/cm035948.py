async def test_exception_handling_posts_error_to_github(
        self,
        mock_get_app_conversation_info_service,
        mock_get_sandbox_service,
        mock_get_httpx_client,
        mock_get_summary_instruction,
        github_callback_processor,
        conversation_state_update_event,
        event_callback,
        mock_app_conversation_info,
        mock_sandbox_info,
    ):
        conversation_id = uuid4()

        # happy-ish path, except httpx error
        mock_httpx_client = await _setup_happy_path_services(
            mock_get_app_conversation_info_service,
            mock_get_sandbox_service,
            mock_get_httpx_client,
            mock_app_conversation_info,
            mock_sandbox_info,
        )
        mock_httpx_client.post.side_effect = Exception('Simulated agent server error')
        mock_get_summary_instruction.return_value = 'Please provide a summary'

        with (
            patch(
                'integrations.github.github_v1_callback_processor.GithubIntegration'
            ) as mock_github_integration,
            patch(
                'integrations.github.github_v1_callback_processor.Github'
            ) as mock_github,
        ):
            mock_integration = MagicMock()
            mock_github_integration.return_value = mock_integration
            mock_integration.get_access_token.return_value.token = 'test_token'

            mock_gh = MagicMock()
            mock_github.return_value.__enter__.return_value = mock_gh
            mock_repo = MagicMock()
            mock_issue = MagicMock()
            mock_repo.get_issue.return_value = mock_issue
            mock_gh.get_repo.return_value = mock_repo

            result = await github_callback_processor(
                conversation_id=conversation_id,
                callback=event_callback,
                event=conversation_state_update_event,
            )

        assert result is not None
        assert result.status == EventCallbackResultStatus.ERROR
        assert 'Simulated agent server error' in result.detail

        mock_issue.create_comment.assert_called_once()
        call_args = mock_issue.create_comment.call_args
        error_comment = call_args[1].get('body') or call_args[0][0]
        assert (
            'OpenHands encountered an error: **Simulated agent server error**'
            in error_comment
        )
        assert f'conversations/{conversation_id}' in error_comment
        assert 'for more information.' in error_comment