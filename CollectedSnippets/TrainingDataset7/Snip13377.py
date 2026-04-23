def render(self, context):
        for condition, nodelist in self.conditions_nodelists:
            if condition is not None:  # if / elif clause
                try:
                    match = condition.eval(context)
                except VariableDoesNotExist:
                    match = None
            else:  # else clause
                match = True

            if match:
                return nodelist.render(context)

        return ""