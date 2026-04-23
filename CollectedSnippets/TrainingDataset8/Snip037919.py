def __init__(self, st_func_name, cached_func):
        msg = self._get_message(st_func_name, cached_func)
        super(CachedStFunctionWarning, self).__init__(msg)