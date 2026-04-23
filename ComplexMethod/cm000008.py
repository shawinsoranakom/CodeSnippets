def _is_bold_marker(node: SyntaxTreeNode) -> str | None:
    """Detect a bold-only paragraph used as a group marker.

    Pattern: a paragraph whose only content is **Group Name** (possibly
    surrounded by empty text nodes in the AST).
    Returns the group name text, or None if not a group marker.
    """
    if node.type != "paragraph":
        return None
    for child in node.children:
        if child.type != "inline":
            continue
        # Filter out empty text nodes that markdown-it inserts around strong
        meaningful = [c for c in child.children if not (c.type == "text" and c.content == "")]
        if len(meaningful) == 1 and meaningful[0].type == "strong":
            return render_inline_text(meaningful[0].children)
    return None