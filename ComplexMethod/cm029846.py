def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None, context=None):
        """This constructor should always be called with keyword arguments. Arguments are:

        *group* should be None; reserved for future extension when a ThreadGroup
        class is implemented.

        *target* is the callable object to be invoked by the run()
        method. Defaults to None, meaning nothing is called.

        *name* is the thread name. By default, a unique name is constructed of
        the form "Thread-N" where N is a small decimal number.

        *args* is a list or tuple of arguments for the target invocation. Defaults to ().

        *kwargs* is a dictionary of keyword arguments for the target
        invocation. Defaults to {}.

        *context* is the contextvars.Context value to use for the thread.
        The default value is None, which means to check
        sys.flags.thread_inherit_context.  If that flag is true, use a copy
        of the context of the caller.  If false, use an empty context.  To
        explicitly start with an empty context, pass a new instance of
        contextvars.Context().  To explicitly start with a copy of the current
        context, pass the value from contextvars.copy_context().

        If a subclass overrides the constructor, it must make sure to invoke
        the base class constructor (Thread.__init__()) before doing anything
        else to the thread.

        """
        assert group is None, "group argument must be None for now"
        if kwargs is None:
            kwargs = {}
        if name:
            name = str(name)
        else:
            name = _newname("Thread-%d")
            if target is not None:
                try:
                    target_name = target.__name__
                    name += f" ({target_name})"
                except AttributeError:
                    pass

        self._target = target
        self._name = name
        self._args = args
        self._kwargs = kwargs
        if daemon is not None:
            if daemon and not _daemon_threads_allowed():
                raise RuntimeError('daemon threads are disabled in this (sub)interpreter')
            self._daemonic = daemon
        else:
            self._daemonic = current_thread().daemon
        self._context = context
        self._ident = None
        if _HAVE_THREAD_NATIVE_ID:
            self._native_id = None
        self._os_thread_handle = _ThreadHandle()
        self._started = Event()
        self._initialized = True
        # Copy of sys.stderr used by self._invoke_excepthook()
        self._stderr = _sys.stderr
        self._invoke_excepthook = _make_invoke_excepthook()
        # For debugging and _after_fork()
        _dangling.add(self)