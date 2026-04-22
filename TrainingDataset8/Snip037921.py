def __init__(self, orig_exc):
        msg = self._get_message(orig_exc)
        super(CachedObjectMutationWarning, self).__init__(msg)