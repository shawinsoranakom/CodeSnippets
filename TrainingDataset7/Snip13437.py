def get_resolved_arguments(self, context):
        resolved_args = [var.resolve(context) for var in self.args]
        if self.takes_context:
            resolved_args = [context, *resolved_args]
        resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        return resolved_args, resolved_kwargs