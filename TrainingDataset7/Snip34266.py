def test_no_render_side_effect(self):
        """
        #23441 -- InclusionNode shouldn't modify its nodelist at render time.
        """
        engine = Engine(app_dirs=True, libraries=LIBRARIES)
        template = engine.from_string("{% load inclusion %}{% inclusion_no_params %}")
        count = template.nodelist.get_nodes_by_type(Node)
        template.render(Context({}))
        self.assertEqual(template.nodelist.get_nodes_by_type(Node), count)