def test_node_origin(self):
        """
        #25848 -- Set origin on Node so debugging tools can determine which
        template the node came from even if extending or including templates.
        """
        template = self._engine().from_string("content")
        for node in template.nodelist:
            self.assertEqual(node.origin, template.origin)