def parse_google_docstring(docstring: str | None) -> ParsedDocstring:
    """Parse a Google-style docstring into structured data."""
    if not docstring:
        return ParsedDocstring()

    lines = textwrap.dedent(docstring).splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return ParsedDocstring()

    summary = _normalize_text(lines[0].strip())
    body = lines[1:]

    sections: defaultdict[str, list[str]] = defaultdict(list)
    current = "description"
    for line in body:
        stripped = line.strip()
        key = SECTION_ALIASES.get(stripped.rstrip(":").lower())
        if key and stripped.endswith(":"):
            current = key
            continue
        if current != "methods":  # ignore "Methods:" sections; methods are rendered from AST
            sections[current].append(line)

    description = "\n".join(sections.pop("description", [])).strip("\n")
    description = _normalize_text(description)

    return ParsedDocstring(
        summary=summary,
        description=description,
        params=_parse_named_entries(sections.get("params", [])),
        attributes=_parse_named_entries(sections.get("attributes", [])),
        returns=_parse_returns(sections.get("returns", [])),
        yields=_parse_returns(sections.get("yields", [])),
        raises=_parse_named_entries(sections.get("raises", [])),
        notes=[textwrap.dedent("\n".join(sections.get("notes", []))).strip()] if sections.get("notes") else [],
        examples=[textwrap.dedent("\n".join(sections.get("examples", []))).strip()] if sections.get("examples") else [],
        references=[line.strip() for line in sections.get("references", []) if line.strip()],
    )