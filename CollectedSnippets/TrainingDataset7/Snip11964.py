def earliest(self, *fields):
        if self.query.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self._earliest(*fields)