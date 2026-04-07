def _listarr(self, func):
        """
        Return a sequence (list) corresponding with the given function.
        Return a numpy array if possible.
        """
        lst = [func(i) for i in range(len(self))]
        if numpy:
            return numpy.array(lst)  # ARRRR!
        else:
            return lst