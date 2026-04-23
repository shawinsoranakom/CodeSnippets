def test_construct_initial_message_with_plugin_params_creates_new_message(self):
        """Test _construct_initial_message_with_plugin_params creates message when no initial message."""
        from openhands.agent_server.models import TextContent
        from openhands.app_server.app_conversation.app_conversation_models import (
            PluginSpec,
        )

        plugins = [
            PluginSpec(
                source='github:owner/repo',
                parameters={'api_key': 'test123', 'debug': True},
            )
        ]

        result = self.service._construct_initial_message_with_plugin_params(
            None, plugins
        )

        assert result is not None
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        assert 'Plugin Configuration Parameters:' in result.content[0].text
        assert '- api_key: test123' in result.content[0].text
        assert '- debug: True' in result.content[0].text
        assert result.run is True