def _get_action_description(func, name):
        try:
            return func.short_description
        except AttributeError:
            return capfirst(name.replace("_", " "))