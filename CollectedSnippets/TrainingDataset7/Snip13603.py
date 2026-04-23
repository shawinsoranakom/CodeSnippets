def render(self, context):
        old_setting = context.use_tz
        context.use_tz = self.use_tz
        output = self.nodelist.render(context)
        context.use_tz = old_setting
        return output