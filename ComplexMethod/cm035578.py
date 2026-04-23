async def test_configure_llm_and_mcp_with_custom_model(self):
        """Test _configure_llm_and_mcp with custom LLM model."""
        # Arrange
        custom_model = 'gpt-3.5-turbo'
        self.mock_user_context.get_mcp_api_key.return_value = 'mcp_api_key'

        # Act
        llm, mcp_config = await self.service._configure_llm_and_mcp(
            self.mock_user, custom_model, self.conversation_id
        )

        # Assert
        assert isinstance(llm, LLM)
        assert llm.model == custom_model
        assert llm.base_url == self.mock_user.llm_base_url
        assert llm.api_key.get_secret_value() == self.mock_user.llm_api_key
        assert llm.usage_id == 'agent'

        assert 'mcpServers' in mcp_config
        assert 'default' in mcp_config['mcpServers']
        assert (
            mcp_config['mcpServers']['default']['url']
            == 'https://test.example.com/mcp/mcp'
        )
        assert mcp_config['mcpServers']['default']['headers'][
            'X-OpenHands-ServerConversation-ID'
        ] == str(self.conversation_id)
        assert (
            mcp_config['mcpServers']['default']['headers']['X-Session-API-Key']
            == 'mcp_api_key'
        )