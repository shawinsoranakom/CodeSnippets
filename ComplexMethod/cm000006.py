def _render_inline(children: list[SyntaxTreeNode], *, html: bool) -> str:
    """Render inline AST nodes to HTML or plain text."""
    parts: list[str] = []
    for child in children:
        match child.type:
            case "text":
                parts.append(str(escape(child.content)) if html else child.content)
            case "html_inline":
                if html:
                    parts.append(str(escape(child.content)))
            case "softbreak":
                parts.append(" ")
            case "code_inline":
                parts.append(f"<code>{escape(child.content)}</code>" if html else child.content)
            case "link":
                inner = _render_inline(child.children, html=html)
                if html:
                    href = str(escape(_href(child)))
                    parts.append(f'<a href="{href}" target="_blank" rel="noopener">{inner}</a>')
                else:
                    parts.append(inner)
            case "em":
                inner = _render_inline(child.children, html=html)
                parts.append(f"<em>{inner}</em>" if html else inner)
            case "strong":
                inner = _render_inline(child.children, html=html)
                parts.append(f"<strong>{inner}</strong>" if html else inner)
    return "".join(parts)