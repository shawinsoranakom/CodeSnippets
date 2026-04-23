def _format_links(
    links: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
) -> str:
    if not links:
        return "<links>\n</links>"
    name_by_id = {n.get("id"): _node_display_name(n) for n in nodes}
    visible = links[:_MAX_LINKS]
    lines = []
    for link in visible:
        src_id = link.get("source_id") or ""
        dst_id = link.get("sink_id") or ""
        src_name = name_by_id.get(src_id, src_id)
        dst_name = name_by_id.get(dst_id, dst_id)
        src_out = link.get("source_name") or ""
        dst_in = link.get("sink_name") or ""
        lines.append(
            f"- {_sanitize_for_xml(src_name)}.{_sanitize_for_xml(src_out)} "
            f"-> {_sanitize_for_xml(dst_name)}.{_sanitize_for_xml(dst_in)}"
        )
    extra = len(links) - len(visible)
    if extra > 0:
        lines.append(f"({extra} more not shown)")
    body = "\n".join(lines)
    return f"<links>\n{body}\n</links>"