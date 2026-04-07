def test_template_not_used_pass(self):
        with self.assertTemplateNotUsed("hello"):
            render_to_string("template_used/partials.html#hello")