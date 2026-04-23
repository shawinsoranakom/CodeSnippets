def __init__(self, orig_exc, failed_obj):
        msg = self._get_message(orig_exc, failed_obj)
        super(UnhashableTypeError, self).__init__(msg)
        self.with_traceback(orig_exc.__traceback__)