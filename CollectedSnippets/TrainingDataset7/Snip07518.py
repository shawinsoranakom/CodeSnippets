def ptr(self):
        # Raise an exception if the pointer isn't valid so that NULL pointers
        # aren't passed to routines -- that's very bad.
        if self._ptr:
            return self._ptr
        raise self.null_ptr_exception_class(
            "NULL %s pointer encountered." % self.__class__.__name__
        )