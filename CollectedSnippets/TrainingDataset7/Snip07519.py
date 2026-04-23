def ptr(self, ptr):
        # Only allow the pointer to be set with pointers of the compatible
        # type or None (NULL).
        if not (ptr is None or isinstance(ptr, self.ptr_type)):
            raise TypeError("Incompatible pointer type: %s." % type(ptr))
        self._ptr = ptr