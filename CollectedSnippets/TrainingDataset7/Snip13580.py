def render(self, context):
        old_setting = context.use_l10n
        context.use_l10n = self.use_l10n
        output = self.nodelist.render(context)
        context.use_l10n = old_setting
        return output