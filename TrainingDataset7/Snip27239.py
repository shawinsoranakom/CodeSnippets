def test_dummynode_repr(self):
        node = DummyNode(
            key=("app_a", "0001"),
            origin="app_a.0001",
            error_message="x is missing",
        )
        self.assertEqual(repr(node), "<DummyNode: ('app_a', '0001')>")