def assertTemplateSyntaxError(self, template_name, context, expected):
        with self.assertRaisesMessage(TemplateSyntaxError, expected):
            self.engine.render_to_string(template_name, context)