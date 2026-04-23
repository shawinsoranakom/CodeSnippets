def __init__(self):
        self.cached_func_stack: List[Callable[..., Any]] = []
        self.suppress_st_function_warning = 0