def test_no_malformed_entry_lines(self):
        """Detect list items that look like entries but have broken link syntax.

        Walks the markdown-it AST for list items whose inline text starts
        with '[' but contain no link node. This catches broken markdown
        like '- [name(url)' where the closing '](' is missing.
        """
        md = MarkdownIt("commonmark")
        root = SyntaxTreeNode(md.parse(self.readme_text))

        # Find category section boundaries (between --- and # Resources/Contributing)
        hr_idx = None
        end_idx = None
        for i, node in enumerate(root.children):
            if hr_idx is None and node.type == "hr":
                hr_idx = i
            elif node.type == "heading" and node.tag == "h1":
                text = render_inline_text(node.children[0].children) if node.children else ""
                if end_idx is None and text in ("Resources", "Contributing"):
                    end_idx = i
        if hr_idx is None:
            return

        bad = []
        cat_nodes = root.children[hr_idx + 1 : end_idx or len(root.children)]
        for node in cat_nodes:
            if node.type != "bullet_list":
                continue
            self._check_list_for_broken_links(node, bad)

        assert bad == [], "List items with broken link syntax:\n" + "\n".join(bad)