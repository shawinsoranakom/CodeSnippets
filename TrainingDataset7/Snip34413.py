def test_ifchanged(self):
        template = self.engine.from_string("{% ifchanged x %}{{ a }}{% endifchanged %}")
        vars = template.nodelist.get_nodes_by_type(VariableNode)
        self.assertEqual(len(vars), 1)