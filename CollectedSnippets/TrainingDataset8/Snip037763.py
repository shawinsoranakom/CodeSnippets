def __init__(self, cache_type: CacheType):
        self._cached_func_stack: List[types.FunctionType] = []
        self._suppress_st_function_warning = 0
        self._cache_type = cache_type
        self._allow_widgets: int = 0