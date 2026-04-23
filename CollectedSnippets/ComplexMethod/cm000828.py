async def test_system_prompt_suffix_contains_only_static_content():
    session = _session("graph-1")
    with patch(
        "backend.copilot.builder_context._load_guide",
        return_value="# Guide body",
    ):
        suffix = await build_builder_system_prompt_suffix(session)

    assert suffix.startswith("\n\n")
    assert f"<{BUILDER_SESSION_TAG}>" in suffix
    assert f"</{BUILDER_SESSION_TAG}>" in suffix
    assert "<building_guide>" in suffix
    assert "# Guide body" in suffix
    # Dispatch-mode guidance must appear so the LLM knows to prefer
    # wait_for_result=0 for real runs (builder UI subscribes live) and
    # wait_for_result=120 for dry-runs (so it can inspect the node trace).
    assert "<run_agent_dispatch_mode>" in suffix
    assert "wait_for_result=0" in suffix
    assert "wait_for_result=120" in suffix
    # Regression: dynamic graph id/name must NOT leak into the cacheable
    # suffix — they live in the per-turn prefix so renames and cross-graph
    # sessions don't invalidate Claude's prompt cache.
    assert "graph-1" not in suffix
    assert "id=" not in suffix
    assert "name=" not in suffix