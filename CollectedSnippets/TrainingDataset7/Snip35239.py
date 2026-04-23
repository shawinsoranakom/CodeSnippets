def test_count(self):
        with self.assertTemplateUsed("template_used/base.html", count=2):
            render_to_string("template_used/base.html")
            render_to_string("template_used/base.html")

        msg = (
            "Template 'template_used/base.html' was expected to be rendered "
            "3 time(s) but was actually rendered 2 time(s)."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html", count=3):
                render_to_string("template_used/base.html")
                render_to_string("template_used/base.html")