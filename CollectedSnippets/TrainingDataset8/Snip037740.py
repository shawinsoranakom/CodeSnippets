def __init__(
        self,
        cache_type: CacheType,
        func: types.FunctionType,
        arg_name: Optional[str],
        arg_value: Any,
        orig_exc: BaseException,
    ):
        msg = self._create_message(cache_type, func, arg_name, arg_value)
        super().__init__(msg)
        self.with_traceback(orig_exc.__traceback__)