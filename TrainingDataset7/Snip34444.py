def override_get_template(self, **kwargs):
        class TemplateWithCustomAttrs:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

            def render(self, context):
                return "rendered content"

        template = TemplateWithCustomAttrs(**kwargs)
        origin = self.id()
        return mock.patch.object(
            engine.engine,
            "find_template",
            return_value=(template, origin),
        )