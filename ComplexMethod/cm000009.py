def parse_sponsors(text: str) -> list[ParsedSponsor]:
    """Parse the `# Sponsors` section of README.md into a list of sponsors.

    Expects bullets in the form `**[name](url)**: description`.
    Returns [] if no Sponsors section exists.
    """
    md = MarkdownIt("commonmark")
    tokens = md.parse(text)
    root = SyntaxTreeNode(tokens)
    children = root.children

    start_idx = None
    end_idx = len(children)
    for i, node in enumerate(children):
        if node.type == "heading" and node.tag == "h1":
            title = _heading_text(node).strip().lower()
            if start_idx is None and title == "sponsors":
                start_idx = i + 1
            elif start_idx is not None:
                end_idx = i
                break
    if start_idx is None:
        return []

    sponsors: list[ParsedSponsor] = []
    for node in children[start_idx:end_idx]:
        if node.type != "bullet_list":
            continue
        for list_item in node.children:
            if list_item.type != "list_item":
                continue
            inline = _find_inline(list_item)
            if inline is None:
                continue
            sponsor = _parse_sponsor_item(inline)
            if sponsor:
                sponsors.append(sponsor)
    return sponsors