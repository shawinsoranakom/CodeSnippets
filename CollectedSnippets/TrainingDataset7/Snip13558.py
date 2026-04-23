def render(self, context):
        lang_code = self.lang_code.resolve(context)
        context[self.variable] = translation.get_language_info(lang_code)
        return ""