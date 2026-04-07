def get_for_id(self, id):
        """
        Lookup a ContentType by ID. Use the same shared cache as get_for_model
        (though ContentTypes are not created on-the-fly by get_by_id).
        """
        try:
            ct = self._cache[self.db][id]
        except KeyError:
            # This could raise a DoesNotExist; that's correct behavior and will
            # make sure that only correct ctypes get stored in the cache dict.
            ct = self.get(pk=id)
            self._add_to_cache(self.db, ct)
        return ct