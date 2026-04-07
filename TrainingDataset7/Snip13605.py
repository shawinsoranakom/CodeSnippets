def render(self, context):
        with timezone.override(self.tz.resolve(context)):
            output = self.nodelist.render(context)
        return output