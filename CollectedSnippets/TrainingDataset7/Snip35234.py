def test_nested_usage(self):
        with self.assertTemplateUsed("template_used/base.html"):
            with self.assertTemplateUsed("template_used/include.html"):
                render_to_string("template_used/include.html")

        with self.assertTemplateUsed("template_used/extends.html"):
            with self.assertTemplateUsed("template_used/base.html"):
                render_to_string("template_used/extends.html")

        with self.assertTemplateUsed("template_used/base.html"):
            with self.assertTemplateUsed("template_used/alternative.html"):
                render_to_string("template_used/alternative.html")
            render_to_string("template_used/base.html")

        with self.assertTemplateUsed("template_used/base.html"):
            render_to_string("template_used/extends.html")
            with self.assertTemplateNotUsed("template_used/base.html"):
                render_to_string("template_used/alternative.html")
            render_to_string("template_used/base.html")