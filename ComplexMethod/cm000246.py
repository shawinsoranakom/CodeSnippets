def test_remove(self) -> None:
        t = self._get_binary_search_tree()

        t.remove(13)
        r"""
              8
             / \
            3   10
           / \    \
          1   6    14
             / \
            4   7
             \
              5
        """
        assert t.root is not None
        assert t.root.right is not None
        assert t.root.right.right is not None
        assert t.root.right.right.right is None
        assert t.root.right.right.left is None

        t.remove(7)
        r"""
              8
             / \
            3   10
           / \    \
          1   6    14
             /
            4
             \
              5
        """
        assert t.root.left is not None
        assert t.root.left.right is not None
        assert t.root.left.right.left is not None
        assert t.root.left.right.right is None
        assert t.root.left.right.left.label == 4

        t.remove(6)
        r"""
              8
             / \
            3   10
           / \    \
          1   4    14
               \
                5
        """
        assert t.root.left.left is not None
        assert t.root.left.right.right is not None
        assert t.root.left.left.label == 1
        assert t.root.left.right.label == 4
        assert t.root.left.right.right.label == 5
        assert t.root.left.right.left is None
        assert t.root.left.left.parent == t.root.left
        assert t.root.left.right.parent == t.root.left

        t.remove(3)
        r"""
              8
             / \
            4   10
           / \    \
          1   5    14
        """
        assert t.root is not None
        assert t.root.left.label == 4
        assert t.root.left.right.label == 5
        assert t.root.left.left.label == 1
        assert t.root.left.parent == t.root
        assert t.root.left.left.parent == t.root.left
        assert t.root.left.right.parent == t.root.left

        t.remove(4)
        r"""
              8
             / \
            5   10
           /      \
          1        14
        """
        assert t.root.left is not None
        assert t.root.left.left is not None
        assert t.root.left.label == 5
        assert t.root.left.right is None
        assert t.root.left.left.label == 1
        assert t.root.left.parent == t.root
        assert t.root.left.left.parent == t.root.left