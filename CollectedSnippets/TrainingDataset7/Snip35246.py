def test_template_not_used_pass_non_partial(self):
        with self.assertTemplateNotUsed(
            "template_used/base.html#template_used/base.html"
        ):
            render_to_string("template_used/base.html")