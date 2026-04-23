def _listarr(self, func):
        """
        Internal routine that returns a sequence (list) corresponding with
        the given function.
        """
        return [func(self.ptr, i) for i in range(len(self))]