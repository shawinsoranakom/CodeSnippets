def __init__(self, orig_exc, cached_func_or_code, hash_func=None, lineno=None):
        self.alternate_name = type(orig_exc).__name__

        if hash_func:
            msg = self._get_message_from_func(orig_exc, cached_func_or_code, hash_func)
        else:
            msg = self._get_message_from_code(orig_exc, cached_func_or_code, lineno)

        super(UserHashError, self).__init__(msg)
        self.with_traceback(orig_exc.__traceback__)