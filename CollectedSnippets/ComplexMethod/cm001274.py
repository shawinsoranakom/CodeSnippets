def test_resolve_session_permissions_blocks_out_of_scope_tools() -> None:
    """Builder-bound sessions return a blacklist of the three tools that
    conflict with the panel's graph-bound scope. Regular sessions return
    ``None`` so default (unrestricted) behaviour is preserved."""
    from backend.copilot.builder_context import BUILDER_BLOCKED_TOOLS
    from backend.copilot.model import ChatSession

    unbound = ChatSession.new("u1", dry_run=False)
    assert chat_routes.resolve_session_permissions(unbound) is None

    bound = ChatSession.new("u1", dry_run=False, builder_graph_id="g1")
    perms = chat_routes.resolve_session_permissions(bound)
    assert perms is not None
    assert perms.tools_exclude is True  # blacklist, not whitelist
    assert sorted(perms.tools) == sorted(BUILDER_BLOCKED_TOOLS)
    # Read-side lookups stay available — only write-scope / guide-dup are blocked.
    assert "find_block" not in perms.tools
    assert "find_agent" not in perms.tools
    assert "search_docs" not in perms.tools
    # The write tools (edit_agent / run_agent) are NOT blacklisted — they
    # enforce scope per-tool via the builder_graph_id guard.
    assert "edit_agent" not in perms.tools
    assert "run_agent" not in perms.tools