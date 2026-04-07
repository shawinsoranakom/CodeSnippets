def __init__(self, func, takes_context, args, kwargs, target_var):
        super().__init__(func, takes_context, args, kwargs)
        self.target_var = target_var