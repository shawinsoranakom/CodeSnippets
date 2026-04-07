def render(self, context):
        self.filter_expression.var.translate = not self.noop
        if self.message_context:
            self.filter_expression.var.message_context = self.message_context.resolve(
                context
            )
        output = self.filter_expression.resolve(context)
        value = render_value_in_context(output, context)
        # Restore percent signs. Percent signs in template text are doubled
        # so they are not interpreted as string format flags.
        is_safe = isinstance(value, SafeData)
        value = value.replace("%%", "%")
        value = mark_safe(value) if is_safe else value
        if self.asvar:
            context[self.asvar] = value
            return ""
        else:
            return value