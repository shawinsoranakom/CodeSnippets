async def test_create_entries_cloud_deployment(self, mock_settings, mock_response):
        """Test create_entries in cloud deployment mode."""
        mock_404_response = MagicMock()
        mock_404_response.status_code = 404
        mock_404_response.is_success = False
        mock_404_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message='Not Found', request=MagicMock(), response=mock_404_response
        )

        # Mock user exists check response
        mock_user_exists_response = MagicMock()
        mock_user_exists_response.is_success = True
        mock_user_exists_response.json.return_value = {
            'user_info': {'user_id': 'test-user-id'}
        }

        mock_token_manager = MagicMock()
        mock_token_manager.return_value.get_user_info_from_user_id = AsyncMock(
            return_value={'email': 'test@example.com'}
        )

        mock_client = AsyncMock()
        # First GET is for _get_team (404), second GET is for _user_exists (success)
        mock_client.get.side_effect = [mock_404_response, mock_user_exists_response]
        mock_client.post.return_value = mock_response

        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        with (
            patch.dict(os.environ, {'LOCAL_DEPLOYMENT': ''}),
            patch('storage.lite_llm_manager.LITE_LLM_API_KEY', 'test-key'),
            patch('storage.lite_llm_manager.LITE_LLM_API_URL', 'http://test.com'),
            patch('storage.lite_llm_manager.TokenManager', mock_token_manager),
            patch('httpx.AsyncClient', mock_client_class),
        ):
            result = await LiteLlmManager.create_entries(
                'test-org-id', 'test-user-id', mock_settings, create_user=False
            )

            assert result is not None
            assert _agent_value(result, 'agent') == 'CodeActAgent'
            assert _agent_value(result, 'llm.model') == get_default_litellm_model()
            assert _secret_value(result, 'llm.api_key') == 'test-api-key'
            assert _agent_value(result, 'llm.base_url') == 'http://test.com'

            # Verify API calls were made (get_team + user_exists + 4 posts)
            assert mock_client.get.call_count == 2  # get_team + user_exists
            assert (
                mock_client.post.call_count == 4
            )