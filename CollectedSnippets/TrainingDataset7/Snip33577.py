def test_extends_node_repr(self):
        extends_node = ExtendsNode(
            nodelist=NodeList([]),
            parent_name=Node(),
            template_dirs=[],
        )
        self.assertEqual(repr(extends_node), "<ExtendsNode: extends None>")