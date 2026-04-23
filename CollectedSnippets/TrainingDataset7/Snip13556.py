def render(self, context):
        context[self.variable] = [
            (k, translation.gettext(v)) for k, v in settings.LANGUAGES
        ]
        return ""