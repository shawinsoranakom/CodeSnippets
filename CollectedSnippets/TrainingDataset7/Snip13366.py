def render(self, context):
        first = ""
        for var in self.vars:
            value = var.resolve(context, ignore_failures=True)
            if value:
                first = render_value_in_context(value, context)
                break
        if self.asvar:
            context[self.asvar] = first
            return ""
        return first