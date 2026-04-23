def render(self, context):
        langs = self.languages.resolve(context)
        context[self.variable] = [self.get_language_info(lang) for lang in langs]
        return ""