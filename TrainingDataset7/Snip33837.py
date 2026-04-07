def test_repr(self):
        include_node = IncludeNode("app/template.html")
        self.assertEqual(
            repr(include_node),
            "<IncludeNode: template='app/template.html'>",
        )