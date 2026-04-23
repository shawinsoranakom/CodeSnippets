def __del__(self):
        """
        Free the memory used by the C++ object.
        """
        if self.destructor and self._ptr:
            try:
                self.destructor(self.ptr)
            except (AttributeError, ImportError, TypeError):
                pass