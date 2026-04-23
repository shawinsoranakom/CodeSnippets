async def test_migrate_entries_successful_migration(
        self, mock_user_settings, mock_user_response, mock_response
    ):
        """Test successful migrate_entries operation."""
        # Mock response for key list
        mock_key_list_response = MagicMock()
        mock_key_list_response.is_success = True
        mock_key_list_response.status_code = 200
        mock_key_list_response.json.return_value = {
            'keys': ['test-key-1', 'test-key-2'],
            'total_count': 2,
        }
        mock_key_list_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {'LOCAL_DEPLOYMENT': ''}):
            with patch('storage.lite_llm_manager.LITE_LLM_API_KEY', 'test-key'):
                with patch(
                    'storage.lite_llm_manager.LITE_LLM_API_URL', 'http://test.com'
                ):
                    with patch(
                        'storage.lite_llm_manager.TokenManager'
                    ) as mock_token_manager:
                        mock_token_manager.return_value.get_user_info_from_user_id = (
                            AsyncMock(return_value={'email': 'test@example.com'})
                        )

                        with patch('httpx.AsyncClient') as mock_client_class:
                            mock_client = AsyncMock()
                            mock_client_class.return_value.__aenter__.return_value = (
                                mock_client
                            )
                            # First GET is for _get_user, second GET is for _get_user_keys
                            mock_client.get.side_effect = [
                                mock_user_response,
                                mock_key_list_response,
                            ]
                            mock_client.post.return_value = mock_response

                            # Mock verify_key to return True (key exists in LiteLLM)
                            with patch.object(
                                LiteLlmManager, 'verify_key', return_value=True
                            ):
                                result = await LiteLlmManager.migrate_entries(
                                    'test-org-id',
                                    'test-user-id',
                                    mock_user_settings,
                                )

                            # migrate_entries returns the user_settings unchanged
                            assert result is not None
                            effective_settings = result.to_settings()
                            assert (
                                _agent_value(effective_settings, 'agent') == 'TestAgent'
                            )
                            assert (
                                _agent_value(effective_settings, 'llm.model')
                                == 'test-model'
                            )
                            assert result.llm_api_key.get_secret_value() == 'test-key'
                            assert (
                                _agent_value(effective_settings, 'llm.base_url')
                                == 'http://test.com'
                            )

                            # Verify migration steps were called:
                            # - 2 GET requests: _get_user, _get_user_keys
                            # - POST requests: create_team, update_user, add_user_to_team,
                            #   and update_key for each key (2 keys)
                            assert mock_client.get.call_count == 2
                            assert (
                                mock_client.post.call_count == 5
                            )