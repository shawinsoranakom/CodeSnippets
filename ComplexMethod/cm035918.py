async def test_create_entries_inherits_existing_team_budget(
        self, mock_settings, mock_response
    ):
        """Test that create_entries inherits budget from existing team."""
        mock_team_response = MagicMock()
        mock_team_response.is_success = True
        mock_team_response.status_code = 200
        mock_team_response.json.return_value = {
            'team_info': {'max_budget': 30.0, 'spend': 5.0},
            'team_memberships': [],
        }
        mock_team_response.raise_for_status = MagicMock()

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
        # First GET is for _get_team (success), second GET is for _user_exists (success)
        mock_client.get.side_effect = [mock_team_response, mock_user_exists_response]
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

            # Verify _get_team was called first
            assert mock_client.get.call_count == 2  # get_team + user_exists
            get_call_url = mock_client.get.call_args_list[0][0][0]
            assert 'team/info' in get_call_url
            assert 'test-org-id' in get_call_url

            # Verify _create_team was called with inherited budget (30.0)
            create_team_call = mock_client.post.call_args_list[0]
            assert 'team/new' in create_team_call[0][0]
            assert create_team_call[1]['json']['max_budget'] == 30.0

            # Verify _add_user_to_team was called with inherited budget (30.0)
            add_user_call = mock_client.post.call_args_list[1]
            assert 'team/member_add' in add_user_call[0][0]
            assert add_user_call[1]['json']['max_budget_in_team'] == 30.0