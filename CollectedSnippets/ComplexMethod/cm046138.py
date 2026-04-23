def render_summary_tabs(module: DocumentedModule) -> str:
    """Render a tabbed summary of classes, methods, and functions for quick navigation."""
    tab_entries: list[tuple[str, list[str]]] = []

    if module.classes:
        tab_entries.append(
            (
                "Classes",
                [f"- [`{cls.name}`](#{item_anchor(cls)})" for cls in module.classes],
            )
        )

    property_links = []
    method_links = []
    for cls in module.classes:
        for child in cls.children:
            if child.kind == "property":
                property_links.append(f"- [`{cls.name}.{child.name}`](#{item_anchor(child)})")
        for child in cls.children:
            if child.kind == "method":
                method_links.append(f"- [`{cls.name}.{child.name}`](#{item_anchor(child)})")
    if property_links:
        tab_entries.append(("Properties", property_links))
    if method_links:
        tab_entries.append(("Methods", method_links))

    if module.functions:
        tab_entries.append(
            (
                "Functions",
                [f"- [`{func.name}`](#{item_anchor(func)})" for func in module.functions],
            )
        )

    if not tab_entries:
        return ""

    lines = ['!!! abstract "Summary"\n']
    for label, bullets in tab_entries:
        badge_class = SUMMARY_BADGE_MAP.get(label, label.lower())
        label_badge = f'<span class="doc-kind doc-kind-{badge_class}">{label}</span>'
        lines.append(f'    === "{label_badge}"\n')
        lines.append("\n".join(f"        {line}" for line in bullets))
        lines.append("")  # Blank line after each tab block
    return "\n".join(lines).rstrip() + "\n\n"