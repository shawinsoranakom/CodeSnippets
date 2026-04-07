def _get_context_stack_frame(self, context):
        # The Context object behaves like a stack where each template tag can
        # create a new scope. Find the place where to store the state to detect
        # changes.
        if "forloop" in context:
            # Ifchanged is bound to the local for loop.
            # When there is a loop-in-loop, the state is bound to the inner
            # loop, so it resets when the outer loop continues.
            return context["forloop"]
        else:
            # Using ifchanged outside loops. Effectively this is a no-op
            # because the state is associated with 'self'.
            return context.render_context