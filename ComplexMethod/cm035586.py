async def test_build_request_multiple_plugins(self, _mock_tools):
        """Multiple plugins are all converted correctly."""
        from openhands.app_server.app_conversation.app_conversation_models import (
            PluginSpec,
        )

        self.mock_user_context.get_user_info.return_value = self.mock_user

        real_llm = LLM(model='gpt-4', api_key=SecretStr('test-key'))

        self.service._setup_secrets_for_git_providers = AsyncMock(return_value={})
        self.service._configure_llm_and_mcp = AsyncMock(return_value=(real_llm, {}))

        plugins = [
            PluginSpec(source='github:owner/security-plugin', ref='v2.0.0'),
            PluginSpec(
                source='github:owner/monorepo',
                repo_path='plugins/logging',
            ),
            PluginSpec(source='/local/path/to/plugin'),
        ]

        result = await self.service._build_start_conversation_request_for_user(
            sandbox=self.mock_sandbox,
            conversation_id=uuid4(),
            initial_message=None,
            system_message_suffix=None,
            git_provider=None,
            working_dir='/workspace',
            plugins=plugins,
        )

        assert result.plugins is not None
        assert len(result.plugins) == 3
        assert result.plugins[0].source == 'github:owner/security-plugin'
        assert result.plugins[0].ref == 'v2.0.0'
        assert result.plugins[1].source == 'github:owner/monorepo'
        assert result.plugins[1].repo_path == 'plugins/logging'
        assert result.plugins[2].source == '/local/path/to/plugin'