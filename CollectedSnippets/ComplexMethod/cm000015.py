def _check_list_for_broken_links(self, bullet_list, bad):
        for list_item in bullet_list.children:
            if list_item.type != "list_item":
                continue
            inline = _find_inline(list_item)
            if inline is None:
                continue
            # Check if inline text starts with '[' but has no link node
            has_link = any(c.type == "link" for c in inline.children)
            text = render_inline_text(inline.children)
            if not has_link and text.startswith("["):
                line = list_item.map[0] + 1 if list_item.map else "?"
                bad.append(f"  line {line}: {text}")
            # Recurse into nested lists
            for child in list_item.children:
                if child.type == "bullet_list":
                    self._check_list_for_broken_links(child, bad)