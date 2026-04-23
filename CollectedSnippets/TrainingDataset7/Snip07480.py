def __init__(self, func_name):
        # GEOS thread-safe function signatures end with '_r' and take an
        # additional context handle parameter.
        self.cfunc = getattr(lgeos, func_name + "_r")
        # Create a reference to thread_context so it's not garbage-collected
        # before an attempt to call this object.
        self.thread_context = thread_context