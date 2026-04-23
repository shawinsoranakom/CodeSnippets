def _parse_list_entries(
    bullet_list: SyntaxTreeNode,
    *,
    subcategory: str = "",
) -> list[ParsedEntry]:
    """Extract entries from a bullet_list AST node.

    Handles three patterns:
    - Text-only list_item -> subcategory label -> recurse into nested list
    - Link list_item with nested link-only items -> entry with also_see
    - Link list_item without nesting -> simple entry
    """
    entries: list[ParsedEntry] = []

    for list_item in bullet_list.children:
        if list_item.type != "list_item":
            continue

        inline = _find_inline(list_item)
        if inline is None:
            continue

        first_link = _find_child(inline, "link")

        if first_link is None or inline.children[0] is not first_link:
            # Subcategory label: take text before the first link, strip trailing separators
            pre_link = []
            for child in inline.children:
                if child.type == "link":
                    break
                pre_link.append(child)
            label = _SUBCAT_TRAILING_RE.sub("", render_inline_text(pre_link)) if pre_link else render_inline_text(inline.children)
            nested = _find_child(list_item, "bullet_list")
            if nested:
                entries.extend(_parse_list_entries(nested, subcategory=label))
            continue

        # Entry with a link
        name = render_inline_text(first_link.children)
        url = _href(first_link)
        desc_html = _extract_description_html(inline, first_link)

        # Collect also_see from nested bullet_list
        also_see: list[AlsoSee] = []
        nested = _find_child(list_item, "bullet_list")
        if nested:
            for sub_item in nested.children:
                if sub_item.type != "list_item":
                    continue
                sub_inline = _find_inline(sub_item)
                if sub_inline:
                    sub_link = _find_child(sub_inline, "link")
                    if sub_link:
                        also_see.append(AlsoSee(
                            name=render_inline_text(sub_link.children),
                            url=_href(sub_link),
                        ))

        entries.append(ParsedEntry(
            name=name,
            url=url,
            description=desc_html,
            also_see=also_see,
            subcategory=subcategory,
        ))

    return entries