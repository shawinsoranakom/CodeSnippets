def test_remove_2(self) -> None:
        t = self._get_binary_search_tree()

        t.remove(3)
        r"""
              8
             / \
            4   10
           / \    \
          1   6    14
             / \   /
            5   7 13
        """
        assert t.root is not None
        assert t.root.left is not None
        assert t.root.left.left is not None
        assert t.root.left.right is not None
        assert t.root.left.right.left is not None
        assert t.root.left.right.right is not None
        assert t.root.left.label == 4
        assert t.root.left.right.label == 6
        assert t.root.left.left.label == 1
        assert t.root.left.right.right.label == 7
        assert t.root.left.right.left.label == 5
        assert t.root.left.parent == t.root
        assert t.root.left.right.parent == t.root.left
        assert t.root.left.left.parent == t.root.left
        assert t.root.left.right.left.parent == t.root.left.right