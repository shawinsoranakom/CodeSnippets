def test_verbatim_tag06(self):
        output = self.engine.render_to_string("verbatim-tag06")
        self.assertEqual(output, "Don't {% endverbatim %} just yet")