def render(self, context):
        return self.nodelist.render(context) if self.inline else ""