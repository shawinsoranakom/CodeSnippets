def test_repr(self):
        static_node = StaticNode(varname="named-var", path="named-path")
        self.assertEqual(
            repr(static_node),
            "StaticNode(varname='named-var', path='named-path')",
        )
        static_node = StaticNode(path="named-path")
        self.assertEqual(
            repr(static_node),
            "StaticNode(varname=None, path='named-path')",
        )