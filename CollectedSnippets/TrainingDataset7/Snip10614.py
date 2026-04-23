def __hash__(self):
        if not self._is_pk_set():
            raise TypeError("Model instances without primary key value are unhashable")
        return hash(self.pk)