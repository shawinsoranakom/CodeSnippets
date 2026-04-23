def test_agent_script_structure_and_syntax(self, simple_agent_script_content):
        """Test that the agent script has correct structure and valid syntax."""
        import ast

        # Test syntax is valid
        try:
            ast.parse(simple_agent_script_content)
        except SyntaxError as e:
            pytest.fail(f"Script has invalid syntax: {e}")

        # Test key components are present
        assert "from lfx import components as cp" in simple_agent_script_content
        assert "cp.ChatInput()" in simple_agent_script_content
        assert "cp.AgentComponent()" in simple_agent_script_content
        assert "cp.URLComponent()" in simple_agent_script_content
        assert "cp.ChatOutput()" in simple_agent_script_content
        assert "async def get_graph()" in simple_agent_script_content
        assert "await url_component.to_toolkit()" in simple_agent_script_content
        assert 'model_name="gpt-4o-mini"' in simple_agent_script_content
        assert 'agent_llm="OpenAI"' in simple_agent_script_content
        assert "return Graph(chat_input, chat_output" in simple_agent_script_content