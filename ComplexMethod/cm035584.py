def test_construct_initial_message_with_multiple_plugins(self):
        """Test _construct_initial_message_with_plugin_params handles multiple plugins."""
        from openhands.agent_server.models import TextContent
        from openhands.app_server.app_conversation.app_conversation_models import (
            PluginSpec,
        )

        plugins = [
            PluginSpec(
                source='github:owner/plugin1',
                parameters={'key1': 'value1'},
            ),
            PluginSpec(
                source='github:owner/plugin2',
                parameters={'key2': 'value2'},
            ),
        ]

        result = self.service._construct_initial_message_with_plugin_params(
            None, plugins
        )

        assert result is not None
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        text = result.content[0].text
        assert 'Plugin Configuration Parameters:' in text
        # Multiple plugins should show grouped by plugin name
        assert 'plugin1' in text
        assert 'plugin2' in text
        assert 'key1: value1' in text
        assert 'key2: value2' in text