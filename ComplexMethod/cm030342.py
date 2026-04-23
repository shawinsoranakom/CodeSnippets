def __init__(self, kind, value, maxvalue, *, ctx):
        if ctx is None:
            ctx = context._default_context.get_context()
        self._is_fork_ctx = ctx.get_start_method() == 'fork'
        unlink_now = sys.platform == 'win32' or self._is_fork_ctx
        for i in range(100):
            try:
                sl = self._semlock = _multiprocessing.SemLock(
                    kind, value, maxvalue, self._make_name(),
                    unlink_now)
            except FileExistsError:
                pass
            else:
                break
        else:
            raise FileExistsError('cannot find name for semaphore')

        util.debug('created semlock with handle %s' % sl.handle)
        self._make_methods()

        if sys.platform != 'win32':
            def _after_fork(obj):
                obj._semlock._after_fork()
            util.register_after_fork(self, _after_fork)

        if self._semlock.name is not None:
            # We only get here if we are on Unix with forking
            # disabled.  When the object is garbage collected or the
            # process shuts down we unlink the semaphore name
            from .resource_tracker import register
            register(self._semlock.name, "semaphore")
            util.Finalize(self, SemLock._cleanup, (self._semlock.name,),
                          exitpriority=0)