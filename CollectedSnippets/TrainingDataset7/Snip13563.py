def render(self, context):
        context[self.variable] = translation.get_language()
        return ""