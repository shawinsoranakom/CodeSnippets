def __init__(self, var, name, nodelist, extra_context=None):
        self.nodelist = nodelist
        # var and name are legacy attributes, being left in case they are used
        # by third-party subclasses of this Node.
        self.extra_context = extra_context or {}
        if name:
            self.extra_context[name] = var