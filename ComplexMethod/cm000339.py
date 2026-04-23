def test_sdm_with_user_set_bounded_iterations(self):
        """User-set bounded iterations are preserved through fix pipeline."""
        agent = _make_orchestrator_agent()
        # Simulate user setting bounded iterations
        for node in agent["nodes"]:
            if node["block_id"] == TOOL_ORCHESTRATOR_BLOCK_ID:
                node["input_default"]["agent_mode_max_iterations"] = 5
                node["input_default"]["sys_prompt"] = "You are a helpful orchestrator"

        fixer = AgentFixer()
        fixed = fixer.apply_all_fixes(agent)

        sdm = next(
            n for n in fixed["nodes"] if n["block_id"] == TOOL_ORCHESTRATOR_BLOCK_ID
        )
        assert sdm["input_default"]["agent_mode_max_iterations"] == 5
        assert sdm["input_default"]["sys_prompt"] == "You are a helpful orchestrator"
        # Other defaults still filled
        assert sdm["input_default"]["conversation_compaction"] is True
        assert sdm["input_default"]["retry"] == 3