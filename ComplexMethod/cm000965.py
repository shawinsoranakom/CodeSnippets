async def test_guide_lives_in_system_prompt_not_user_message(self):
        from backend.copilot.builder_context import (
            BUILDER_CONTEXT_TAG,
            BUILDER_SESSION_TAG,
            build_builder_context_turn_prefix,
            build_builder_system_prompt_suffix,
        )
        from backend.copilot.model import ChatSession

        session = MagicMock(spec=ChatSession)
        session.session_id = "s"
        session.metadata = MagicMock()
        session.metadata.builder_graph_id = "graph-1"

        agent_json = {
            "id": "graph-1",
            "name": "Demo",
            "version": 7,
            "nodes": [
                {
                    "id": "n1",
                    "block_id": "block-A",
                    "input_default": {"name": "Input"},
                    "metadata": {},
                }
            ],
            "links": [],
        }
        guide_body = "# UNIQUE_GUIDE_MARKER body"
        with (
            patch(
                "backend.copilot.builder_context.get_agent_as_json",
                new=AsyncMock(return_value=agent_json),
            ),
            patch(
                "backend.copilot.builder_context._load_guide",
                return_value=guide_body,
            ),
        ):
            suffix = await build_builder_system_prompt_suffix(session)
            prefix = await build_builder_context_turn_prefix(session, "user-1")

        # System prompt suffix carries <builder_session> and the guide.
        assert f"<{BUILDER_SESSION_TAG}>" in suffix
        assert guide_body in suffix
        # Dynamic bits must NOT be in the suffix — otherwise renames and
        # cross-graph sessions invalidate Claude's prompt cache.
        assert "graph-1" not in suffix
        assert "Demo" not in suffix

        # Per-turn prefix carries <builder_context> with the full live
        # snapshot (id, name, version, nodes) but NEVER the guide.
        assert f"<{BUILDER_CONTEXT_TAG}>" in prefix
        assert 'id="graph-1"' in prefix
        assert 'name="Demo"' in prefix
        assert 'version="7"' in prefix
        assert guide_body not in prefix
        assert "<building_guide>" not in prefix

        # Guide appears in the combined on-the-wire payload exactly ONCE.
        combined = suffix + "\n\n" + prefix
        assert combined.count(guide_body) == 1