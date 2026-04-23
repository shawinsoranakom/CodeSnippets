def parse_readme(text: str) -> list[ParsedGroup]:
    """Parse README.md text into grouped categories.

    Returns a list of ParsedGroup dicts containing nested categories.
    Content between the thematic break (---) and # Resources or # Contributing
    is parsed as categories grouped by bold markers (**Group Name**).
    """
    md = MarkdownIt("commonmark")
    tokens = md.parse(text)
    root = SyntaxTreeNode(tokens)
    children = root.children

    # Find thematic break (---) and section boundaries in one pass
    hr_idx = None
    cat_end_idx = None
    for i, node in enumerate(children):
        if hr_idx is None and node.type == "hr":
            hr_idx = i
        elif node.type == "heading" and node.tag == "h1":
            text_content = _heading_text(node)
            if cat_end_idx is None and text_content in ("Resources", "Contributing"):
                cat_end_idx = i
    if hr_idx is None:
        return []

    cat_nodes = children[hr_idx + 1 : cat_end_idx or len(children)]
    return _parse_grouped_sections(cat_nodes)