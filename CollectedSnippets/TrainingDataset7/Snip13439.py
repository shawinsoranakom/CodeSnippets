def render(self, context):
        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
        output = self.func(*resolved_args, **resolved_kwargs)
        if self.target_var is not None:
            context[self.target_var] = output
            return ""
        if context.autoescape:
            output = conditional_escape(output)
        return output