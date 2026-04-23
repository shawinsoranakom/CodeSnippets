def __init__(self, func, takes_context, args, kwargs):
        self.func = func
        self.takes_context = takes_context
        self.args = args
        self.kwargs = kwargs