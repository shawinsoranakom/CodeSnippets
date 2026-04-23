def leaf_iter(parent_node, node, level):
        for child_node in node:
            leaf_iter(node, child_node, level if level < 0 else level + 1)

        # Indentation
        if level >= 0:
            indent = '\n' + indent_space * level
            if not node.tail or not node.tail.strip():
                node.tail = '\n' if parent_node is None else indent
            if len(node) > 0:
                if not node.text or not node.text.strip():
                    # First child's indentation is parent's text
                    node.text = indent + indent_space
                last_child = node[-1]
                if last_child.tail == indent + indent_space:
                    # Last child's tail is parent's closing tag indentation
                    last_child.tail = indent

        # Removal condition: node is leaf (not root nor inner node)
        if parent_node is not None and len(node) == 0:
            if remove_blank_text and node.text is not None and not node.text.strip():
                # node.text is None iff node.tag is self-closing (text='' creates closing tag)
                node.text = ''
            if remove_blank_nodes and not (node.text or ''):
                parent_node.remove(node)