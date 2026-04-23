def test_usage(self):
        with self.assertTemplateUsed("template_used/base.html"):
            render_to_string("template_used/base.html")

        with self.assertTemplateUsed(template_name="template_used/base.html"):
            render_to_string("template_used/base.html")

        with self.assertTemplateUsed("template_used/base.html"):
            render_to_string("template_used/include.html")

        with self.assertTemplateUsed("template_used/base.html"):
            render_to_string("template_used/extends.html")

        with self.assertTemplateUsed("template_used/base.html"):
            render_to_string("template_used/base.html")
            render_to_string("template_used/base.html")