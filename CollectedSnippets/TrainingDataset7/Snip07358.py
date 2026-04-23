def _checkdim(self, dim):
        if dim not in (2, 3):
            raise TypeError("Dimension mismatch.")