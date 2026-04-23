def test_put(self) -> None:
        t = BinarySearchTree()
        assert t.is_empty()

        t.put(8)
        r"""
              8
        """
        assert t.root is not None
        assert t.root.parent is None
        assert t.root.label == 8

        t.put(10)
        r"""
              8
               \
                10
        """
        assert t.root.right is not None
        assert t.root.right.parent == t.root
        assert t.root.right.label == 10

        t.put(3)
        r"""
              8
             / \
            3   10
        """
        assert t.root.left is not None
        assert t.root.left.parent == t.root
        assert t.root.left.label == 3

        t.put(6)
        r"""
              8
             / \
            3   10
             \
              6
        """
        assert t.root.left.right is not None
        assert t.root.left.right.parent == t.root.left
        assert t.root.left.right.label == 6

        t.put(1)
        r"""
              8
             / \
            3   10
           / \
          1   6
        """
        assert t.root.left.left is not None
        assert t.root.left.left.parent == t.root.left
        assert t.root.left.left.label == 1

        with pytest.raises(ValueError):
            t.put(1)