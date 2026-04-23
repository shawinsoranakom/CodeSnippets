async def test_build_config_update(self, component_class, default_kwargs):
        """Test that build configuration updates correctly for different model provider selections.

        This test verifies that the component's build configuration is properly
        updated when selecting different model providers using the provider system.
        """
        component = await self.component_setup(component_class, default_kwargs)
        frontend_node = component.to_frontend_node()
        build_config = frontend_node["data"]["node"]["template"]

        # Test that agent_llm field exists and has proper structure
        assert "agent_llm" in build_config
        agent_llm_config = build_config["agent_llm"]
        assert "options" in agent_llm_config
        assert "OpenAI" in agent_llm_config["options"]

        # Test updating build config with OpenAI provider
        updated_config = await component.update_build_config(build_config, "OpenAI", "agent_llm")

        assert "agent_llm" in updated_config
        # When OpenAI is selected, OpenAI-specific fields should be present
        assert "openai_api_key" in updated_config or "model_name" in updated_config

        # Test updating build config with "Custom" (should add input types for LanguageModel)
        updated_config = await component.update_build_config(build_config, "Custom", "agent_llm")
        assert "agent_llm" in updated_config
        assert "LanguageModel" in updated_config["agent_llm"]["input_types"]