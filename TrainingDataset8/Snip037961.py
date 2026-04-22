def __init__(self, orig_exc: BaseException, failed_obj: Any):
        msg = self._get_message(orig_exc, failed_obj)
        super(InternalHashError, self).__init__(msg)
        self.with_traceback(orig_exc.__traceback__)