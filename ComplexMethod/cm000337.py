def test_partial_defaults(self):
        """Only missing fields are filled; existing ones are kept."""
        fixer = AgentFixer()
        agent = {
            "nodes": [
                _make_sdm_node(
                    input_default={
                        "agent_mode_max_iterations": 10,
                    }
                )
            ],
            "links": [],
        }

        result = fixer.fix_orchestrator_blocks(agent)

        defaults = result["nodes"][0]["input_default"]
        assert defaults["agent_mode_max_iterations"] == 10  # kept
        assert defaults["conversation_compaction"] is True  # filled
        assert defaults["retry"] == 3  # filled
        assert defaults["multiple_tool_calls"] is False  # filled
        assert defaults["execution_mode"] == "extended_thinking"  # filled
        assert defaults["model"] == "claude-opus-4-6"  # filled
        assert len(fixer.fixes_applied) == 5