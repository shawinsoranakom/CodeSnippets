def render_docstring(
    doc: ParsedDocstring,
    level: int,
    signature_params: list[ParameterDoc] | None = None,
    section_order: list[str] | None = None,
    extra_sections: dict[str, str] | None = None,
) -> str:
    """Convert a ParsedDocstring into Markdown with tables similar to mkdocstrings."""
    parts: list[str] = []
    if doc.summary:
        parts.append(doc.summary)
    if doc.description:
        parts.append(doc.description)

    sig_params = signature_params or []
    merged_params = _merge_params(doc.params, sig_params)

    sections: dict[str, str] = {}

    if merged_params:
        rows = []
        for p in merged_params:
            default_val = f"`{p.default}`" if p.default not in (None, "") else "*required*"
            rows.append(
                [
                    f"`{p.name}`",
                    f"`{p.type}`" if p.type else "",
                    p.description.strip() if p.description else "",
                    default_val,
                ]
            )
        table = _render_table(["Name", "Type", "Description", "Default"], rows, level, title=None)
        sections["args"] = f"**Args**\n\n{table}"

    if doc.returns:
        rows = []
        for r in doc.returns:
            rows.append([f"`{r.type}`" if r.type else "", r.description])
        table = _render_table(["Type", "Description"], rows, level, title=None)
        sections["returns"] = f"**Returns**\n\n{table}"

    if doc.examples:
        code_block = "\n\n".join(f"```python\n{example.strip()}\n```" for example in doc.examples if example.strip())
        if code_block:
            sections["examples"] = f"**Examples**\n\n{code_block}\n\n"

    if doc.notes:
        note_text = "\n\n".join(doc.notes).strip()
        indented = textwrap.indent(note_text, "    ")
        sections["notes"] = f'!!! note "Notes"\n\n{indented}\n\n'

    if doc.attributes:
        rows = []
        for a in doc.attributes:
            rows.append(
                [f"`{a.name}`", f"`{a.type}`" if a.type else "", a.description.strip() if a.description else ""]
            )
        table = _render_table(["Name", "Type", "Description"], rows, level, title=None)
        sections["attributes"] = f"**Attributes**\n\n{table}"

    if doc.yields:
        rows = []
        for r in doc.yields:
            rows.append([f"`{r.type}`" if r.type else "", r.description])
        table = _render_table(["Type", "Description"], rows, level, title=None)
        sections["yields"] = f"**Yields**\n\n{table}"

    if doc.raises:
        rows = []
        for e in doc.raises:
            type_cell = e.type or e.name
            rows.append([f"`{type_cell}`" if type_cell else "", e.description or ""])
        table = _render_table(["Type", "Description"], rows, level, title=None)
        sections["raises"] = f"**Raises**\n\n{table}"

    if doc.references:
        links = "\n".join(ref if ref.startswith("- ") else f"- {ref}" for ref in doc.references)
        sections["references"] = f"**References**\n\n{links}\n\n"

    if extra_sections:
        sections.update({k: v for k, v in extra_sections.items() if v})
    # Ensure section order contains unique entries to avoid duplicate renders (e.g., classes injecting "examples")
    order = list(dict.fromkeys(section_order or DEFAULT_SECTION_ORDER))

    ordered_sections: list[str] = []
    seen = set()
    for key in order:
        section = sections.get(key)
        if section:
            ordered_sections.append(section)
            seen.add(key)

    for key, section in sections.items():
        if key not in seen:
            ordered_sections.append(section)

    parts.extend(filter(None, ordered_sections))
    return "\n\n".join([p.rstrip() for p in parts if p]).strip() + ("\n\n" if parts else "")