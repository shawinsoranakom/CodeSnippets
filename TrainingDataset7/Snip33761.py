def test_if_tag_shortcircuit01(self):
        """
        If evaluations are shortcircuited where possible
        """
        output = self.engine.render_to_string("if-tag-shortcircuit01", {"x": TestObj()})
        self.assertEqual(output, "yes")