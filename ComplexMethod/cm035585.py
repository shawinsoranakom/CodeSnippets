async def test_build_request_with_plugins(self, _mock_tools):
        """Plugins are converted to PluginSource and included in the request."""
        from openhands.app_server.app_conversation.app_conversation_models import (
            PluginSpec,
        )

        self.mock_user_context.get_user_info.return_value = self.mock_user

        real_llm = LLM(model='gpt-4', api_key=SecretStr('test-key'))

        self.service._setup_secrets_for_git_providers = AsyncMock(return_value={})
        self.service._configure_llm_and_mcp = AsyncMock(return_value=(real_llm, {}))

        plugins = [
            PluginSpec(
                source='github:owner/my-plugin',
                ref='v1.0.0',
                parameters={'api_key': 'test123'},
            )
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

        assert isinstance(result, StartConversationRequest)
        assert result.plugins is not None
        assert len(result.plugins) == 1
        assert result.plugins[0].source == 'github:owner/my-plugin'
        assert result.plugins[0].ref == 'v1.0.0'
        # Plugin params are folded into the initial message
        assert result.initial_message is not None
        assert (
            'Plugin Configuration Parameters:' in result.initial_message.content[0].text
        )
        assert '- api_key: test123' in result.initial_message.content[0].text