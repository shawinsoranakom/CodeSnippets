def render(self, context):
        # Init state storage
        state_frame = self._get_context_stack_frame(context)
        state_frame.setdefault(self)

        nodelist_true_output = None
        if self._varlist:
            # Consider multiple parameters. This behaves like an OR evaluation
            # of the multiple variables.
            compare_to = [
                var.resolve(context, ignore_failures=True) for var in self._varlist
            ]
        else:
            # The "{% ifchanged %}" syntax (without any variables) compares
            # the rendered output.
            compare_to = nodelist_true_output = self.nodelist_true.render(context)

        if compare_to != state_frame[self]:
            state_frame[self] = compare_to
            # render true block if not already rendered
            return nodelist_true_output or self.nodelist_true.render(context)
        elif self.nodelist_false:
            return self.nodelist_false.render(context)
        return ""