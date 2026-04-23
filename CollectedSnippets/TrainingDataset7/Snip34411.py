def test_for(self):
        template = self.engine.from_string("{% for i in 1 %}{{ a }}{% endfor %}")
        vars = template.nodelist.get_nodes_by_type(VariableNode)
        self.assertEqual(len(vars), 1)