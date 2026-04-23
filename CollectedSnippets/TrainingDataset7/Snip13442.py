def __init__(self, func, takes_context, args, kwargs, filename):
        super().__init__(func, takes_context, args, kwargs)
        self.filename = filename