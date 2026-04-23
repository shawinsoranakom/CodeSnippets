def remove_empty_elements_fast(self, root, word_count_threshold=5):
        """
        Remove elements that fall below the desired word threshold in a single pass from the bottom up.
        Skips non-element nodes like HtmlComment and bypasses certain tags that are allowed to have no content.
        """
        bypass_tags = {
            "a",
            "img",
            "br",
            "hr",
            "input",
            "meta",
            "link",
            "source",
            "track",
            "wbr",
            "tr",
            "td",
            "th",
        }

        for el in reversed(list(root.iterdescendants())):
            if not isinstance(el, lhtml.HtmlElement):
                continue

            if el.tag in bypass_tags:
                continue

            # Skip elements inside <pre> or <code> tags where whitespace is significant
            # This preserves whitespace-only spans (e.g., <span class="w"> </span>) in code blocks
            is_in_code_block = False
            ancestor = el.getparent()
            while ancestor is not None:
                if ancestor.tag in ("pre", "code"):
                    is_in_code_block = True
                    break
                ancestor = ancestor.getparent()

            if is_in_code_block:
                continue

            text_content = (el.text_content() or "").strip()
            if (
                len(text_content.split()) < word_count_threshold
                and not el.getchildren()
            ):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)

        return root