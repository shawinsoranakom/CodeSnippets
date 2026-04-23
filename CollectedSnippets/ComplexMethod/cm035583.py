def test_construct_initial_message_with_plugin_params_appends_to_message(self):
        """Test _construct_initial_message_with_plugin_params appends to existing message."""
        from openhands.agent_server.models import SendMessageRequest, TextContent
        from openhands.app_server.app_conversation.app_conversation_models import (
            PluginSpec,
        )

        initial_msg = SendMessageRequest(
            content=[TextContent(text='Please analyze this codebase')],
            run=False,
        )
        plugins = [
            PluginSpec(
                source='github:owner/repo',
                ref='v1.0.0',
                parameters={'target_dir': '/src', 'verbose': True},
            )
        ]

        result = self.service._construct_initial_message_with_plugin_params(
            initial_msg, plugins
        )

        assert result is not None
        assert len(result.content) == 1
        text = result.content[0].text
        assert text.startswith('Please analyze this codebase')
        assert 'Plugin Configuration Parameters:' in text
        assert '- target_dir: /src' in text
        assert '- verbose: True' in text
        assert result.run is False