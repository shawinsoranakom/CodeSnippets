async def build_builder_context_turn_prefix(
    session: ChatSession,
    user_id: str | None,
) -> str:
    """Return the per-turn ``<builder_context>`` prefix with the live
    graph snapshot (id/name/version/nodes/links). ``""`` for non-builder
    sessions; fetch-failure marker if the graph cannot be read."""
    graph_id = session.metadata.builder_graph_id
    if not graph_id:
        return ""

    try:
        agent_json = await get_agent_as_json(graph_id, user_id)
    except Exception:
        logger.exception(
            "[builder_context] Failed to fetch graph %s for session %s",
            graph_id,
            session.session_id,
        )
        return _FETCH_FAILED_PREFIX

    if not agent_json:
        logger.warning(
            "[builder_context] Graph %s not found for session %s",
            graph_id,
            session.session_id,
        )
        return _FETCH_FAILED_PREFIX

    version = _sanitize_for_xml(agent_json.get("version") or "")
    raw_name = agent_json.get("name")
    graph_name = (
        raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else None
    )
    nodes = agent_json.get("nodes") or []
    links = agent_json.get("links") or []
    name_attr = f' name="{_sanitize_for_xml(graph_name)}"' if graph_name else ""
    graph_tag = (
        f'<graph id="{_sanitize_for_xml(graph_id)}"'
        f"{name_attr} "
        f'version="{version}" '
        f'node_count="{len(nodes)}" '
        f'edge_count="{len(links)}"/>'
    )

    inner = f"{graph_tag}\n{_format_nodes(nodes)}\n{_format_links(links, nodes)}"
    return f"<{BUILDER_CONTEXT_TAG}>\n{inner}\n</{BUILDER_CONTEXT_TAG}>\n\n"