async def test_build_start_conversation_request_for_user_integration(
        self, _mock_tools
    ):
        """Test the main _build_start_conversation_request_for_user method integration."""
        self.mock_user_context.get_user_info.return_value = self.mock_user

        mock_secrets = {'GITHUB_TOKEN': StaticSecret(value=SecretStr('tok'))}
        real_llm = LLM(model='gpt-4', api_key=SecretStr('test-key'))
        mock_mcp_config = {'default': {'url': 'test'}}
        test_conversation_id = uuid4()

        self.service._setup_secrets_for_git_providers = AsyncMock(
            return_value=mock_secrets
        )
        self.service._configure_llm_and_mcp = AsyncMock(
            return_value=(real_llm, mock_mcp_config)
        )

        result = await self.service._build_start_conversation_request_for_user(
            sandbox=self.mock_sandbox,
            conversation_id=test_conversation_id,
            initial_message=None,
            system_message_suffix='Test suffix',
            git_provider=ProviderType.GITHUB,
            working_dir='/test/dir',
            agent_type=AgentType.DEFAULT,
            llm_model='gpt-4',
            remote_workspace=None,
            selected_repository='test/repo',
        )

        assert isinstance(result, StartConversationRequest)
        assert result.conversation_id == test_conversation_id
        assert result.agent.llm.model == 'gpt-4'
        # Secrets are injected via agent_context
        assert result.agent.agent_context.secrets == mock_secrets
        # System message suffix includes the original suffix and web host context
        assert 'Test suffix' in result.agent.agent_context.system_message_suffix
        assert '<HOST>' in result.agent.agent_context.system_message_suffix
        assert (
            'https://test.example.com'
            in result.agent.agent_context.system_message_suffix
        )
        # Workspace points to the repo subdirectory
        assert result.workspace.working_dir == '/test/dir/repo'

        self.service._setup_secrets_for_git_providers.assert_called_once_with(
            self.mock_user
        )
        self.service._configure_llm_and_mcp.assert_called_once_with(
            self.mock_user, 'gpt-4', test_conversation_id
        )