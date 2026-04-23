def render(self, context):
        with translation.override(self.language.resolve(context)):
            output = self.nodelist.render(context)
        return output