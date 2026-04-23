def test_fills_defaults_when_missing(self):
        """All agent-mode defaults are populated for a bare SDM node."""
        fixer = AgentFixer()
        agent = {"nodes": [_make_sdm_node()], "links": []}

        result = fixer.fix_orchestrator_blocks(agent)

        defaults = result["nodes"][0]["input_default"]
        assert defaults["agent_mode_max_iterations"] == 10
        assert defaults["conversation_compaction"] is True
        assert defaults["retry"] == 3
        assert defaults["multiple_tool_calls"] is False
        assert defaults["execution_mode"] == "extended_thinking"
        assert defaults["model"] == "claude-opus-4-6"
        assert len(fixer.fixes_applied) == 6