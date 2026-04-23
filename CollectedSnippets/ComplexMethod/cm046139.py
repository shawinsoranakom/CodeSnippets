def render_item(item: DocItem, module_url: str, module_path: str, level: int = 2) -> str:
    """Render a class, function, or method to Markdown."""
    anchor = item_anchor(item)
    title_prefix = item.kind.capitalize()
    anchor_id = anchor.replace("_", r"\_")  # escape underscores so attr_list keeps them in the id
    heading = f"{'#' * level} {title_prefix} `{display_qualname(item)}` {{#{anchor_id}}}"
    signature_block = f"```python\n{item.signature}\n```\n"

    parts = [heading, signature_block]

    if item.bases:
        bases = ", ".join(f"`{b}`" for b in item.bases)
        parts.append(f"**Bases:** {bases}\n")

    # Check for parameters missing type annotations in both signature and docstring
    if item.signature_params and item.doc.params:
        merged = _merge_params(item.doc.params, item.signature_params)
        missing = [p.name for p in merged if not p.type]
        if missing:
            _missing_type_warnings.append(f"{item.qualname}: {', '.join(missing)}")

    if item.kind == "class":
        method_section = None
        if item.children:
            props = [c for c in item.children if c.kind == "property"]
            methods = [c for c in item.children if c.kind == "method"]
            methods.sort(key=lambda m: (not m.name.startswith("__"), m.name))

            rows = []
            for child in props + methods:
                summary = child.doc.summary or (
                    _normalize_text(child.doc.description).split("\n\n")[0] if child.doc.description else ""
                )
                rows.append([f"[`{child.name}`](#{item_anchor(child)})", summary.strip()])
            if rows:
                table = _render_table(["Name", "Description"], rows, level + 1, title=None)
                method_section = f"**Methods**\n\n{table}"

        order = ["args", "attributes", "methods", "examples", *DEFAULT_SECTION_ORDER]
        rendered = render_docstring(
            item.doc,
            level + 1,
            signature_params=item.signature_params,
            section_order=order,
            extra_sections={"methods": method_section} if method_section else None,
        )
        parts.append(rendered)
    else:
        parts.append(render_docstring(item.doc, level + 1, signature_params=item.signature_params))

    if item.kind == "class" and item.source:
        parts.append(render_source_panel(item, module_url, module_path))

    if item.children:
        props = [c for c in item.children if c.kind == "property"]
        methods = [c for c in item.children if c.kind == "method"]
        methods.sort(key=lambda m: (not m.name.startswith("__"), m.name))

        ordered_children = props + methods
        parts.append("<br>\n")
        for idx, child in enumerate(ordered_children):
            parts.append(render_item(child, module_url, module_path, level + 1))
            if idx != len(ordered_children) - 1:
                parts.append("<br>\n")

    if item.source and item.kind != "class":
        parts.append(render_source_panel(item, module_url, module_path))

    return "\n\n".join(p.rstrip() for p in parts if p).rstrip() + "\n\n"