def _format_context(edges, episodes) -> str | None:
    sections: list[str] = []

    if edges:
        fact_lines = []
        for e in edges:
            valid_from, valid_to = extract_temporal_validity(e)
            fact = extract_fact(e)
            fact_lines.append(f"  - {fact} ({valid_from} — {valid_to})")
        sections.append("<FACTS>\n" + "\n".join(fact_lines) + "\n</FACTS>")

    if episodes:
        ep_lines = []
        for ep in episodes:
            # Use raw body (no truncation) for scope parsing — truncated
            # JSON from extract_episode_body() would fail json.loads().
            raw_body = extract_episode_body_raw(ep)
            if _is_non_global_scope(raw_body):
                continue
            display_body = extract_episode_body(ep)
            ts = extract_episode_timestamp(ep)
            ep_lines.append(f"  - [{ts}] {display_body}")
        if ep_lines:
            sections.append(
                "<RECENT_EPISODES>\n" + "\n".join(ep_lines) + "\n</RECENT_EPISODES>"
            )

    if not sections:
        return None

    body = "\n\n".join(sections)
    return f"<temporal_context>\n{body}\n</temporal_context>"