def test_template_used_pass(self):
        with self.assertTemplateUsed("template_used/partials.html#hello"):
            render_to_string("template_used/partials.html#hello")