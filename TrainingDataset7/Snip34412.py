def test_if(self):
        template = self.engine.from_string("{% if x %}{{ a }}{% endif %}")
        vars = template.nodelist.get_nodes_by_type(VariableNode)
        self.assertEqual(len(vars), 1)