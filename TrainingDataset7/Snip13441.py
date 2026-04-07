def get_resolved_arguments(self, context):
        resolved_args, resolved_kwargs = super().get_resolved_arguments(context)

        # Restore the "content" argument.
        # It will move depending on whether takes_context was passed.
        resolved_args.insert(
            1 if self.takes_context else 0, self.nodelist.render(context)
        )

        return resolved_args, resolved_kwargs