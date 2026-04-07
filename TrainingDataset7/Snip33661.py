def test_repr(self):
        node = ForNode(
            "x",
            "sequence",
            is_reversed=True,
            nodelist_loop=["val"],
            nodelist_empty=["val2"],
        )
        self.assertEqual(
            repr(node), "<ForNode: for x in sequence, tail_len: 1 reversed>"
        )