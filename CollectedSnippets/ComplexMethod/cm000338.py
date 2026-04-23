def test_treats_none_values_as_missing(self):
        """Explicit None values are overwritten with defaults."""
        fixer = AgentFixer()
        agent = {
            "nodes": [
                _make_sdm_node(
                    input_default={
                        "agent_mode_max_iterations": None,
                        "conversation_compaction": None,
                        "retry": 3,
                        "multiple_tool_calls": False,
                    }
                )
            ],
            "links": [],
        }

        result = fixer.fix_orchestrator_blocks(agent)

        defaults = result["nodes"][0]["input_default"]
        assert defaults["agent_mode_max_iterations"] == 10  # None -> default
        assert defaults["conversation_compaction"] is True  # None -> default
        assert defaults["retry"] == 3  # kept
        assert defaults["multiple_tool_calls"] is False  # kept
        assert defaults["execution_mode"] == "extended_thinking"  # filled
        assert defaults["model"] == "claude-opus-4-6"  # filled
        assert len(fixer.fixes_applied) == 4