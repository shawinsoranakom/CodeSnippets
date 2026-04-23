def test_if_tag_shortcircuit02(self):
        """
        The is_bad() function should not be evaluated. If it is, an
        exception is raised.
        """
        output = self.engine.render_to_string("if-tag-shortcircuit02", {"x": TestObj()})
        self.assertEqual(output, "no")