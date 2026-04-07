def test_include_template_none(self):
        engine = Engine.get_default()
        outer_temp = engine.from_string("{% include var %}")
        ctx = Context({"var": None})
        msg = "No template names provided"
        with self.assertRaisesMessage(TemplateDoesNotExist, msg):
            outer_temp.render(ctx)