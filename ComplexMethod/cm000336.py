def test_preserves_existing_values(self):
        """Existing user-set values are never overwritten."""
        fixer = AgentFixer()
        agent = {
            "nodes": [
                _make_sdm_node(
                    input_default={
                        "agent_mode_max_iterations": 5,
                        "conversation_compaction": False,
                        "retry": 1,
                        "multiple_tool_calls": True,
                        "execution_mode": "built_in",
                        "model": "gpt-4o",
                    }
                )
            ],
            "links": [],
        }

        result = fixer.fix_orchestrator_blocks(agent)

        defaults = result["nodes"][0]["input_default"]
        assert defaults["agent_mode_max_iterations"] == 5
        assert defaults["conversation_compaction"] is False
        assert defaults["retry"] == 1
        assert defaults["multiple_tool_calls"] is True
        assert defaults["execution_mode"] == "built_in"
        assert defaults["model"] == "gpt-4o"
        assert len(fixer.fixes_applied) == 0