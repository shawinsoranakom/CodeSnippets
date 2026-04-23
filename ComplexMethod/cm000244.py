def remove(self, label: int) -> None:
        """
        Removes a node in the tree

        >>> t = BinarySearchTree()
        >>> t.put(8)
        >>> t.put(10)
        >>> t.remove(8)
        >>> assert t.root.label == 10

        >>> t.remove(3)
        Traceback (most recent call last):
            ...
        ValueError: Node with label 3 does not exist
        """
        node = self.search(label)
        if node.right and node.left:
            lowest_node = self._get_lowest_node(node.right)
            lowest_node.left = node.left
            lowest_node.right = node.right
            node.left.parent = lowest_node
            if node.right:
                node.right.parent = lowest_node
            self._reassign_nodes(node, lowest_node)
        elif not node.right and node.left:
            self._reassign_nodes(node, node.left)
        elif node.right and not node.left:
            self._reassign_nodes(node, node.right)
        else:
            self._reassign_nodes(node, None)