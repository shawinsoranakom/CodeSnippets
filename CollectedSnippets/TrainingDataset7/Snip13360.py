def render(self, context):
        if self not in context.render_context:
            # First time the node is rendered in template
            context.render_context[self] = itertools_cycle(self.cyclevars)
        cycle_iter = context.render_context[self]
        value = next(cycle_iter).resolve(context)
        if self.variable_name:
            context.set_upward(self.variable_name, value)
        if self.silent:
            return ""
        return render_value_in_context(value, context)