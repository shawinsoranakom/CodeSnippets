def reset(self, context):
        """
        Reset the cycle iteration back to the beginning.
        """
        context.render_context[self] = itertools_cycle(self.cyclevars)