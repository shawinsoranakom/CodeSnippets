def get_by_natural_key(self, app_label, model):
        try:
            ct = self._cache[self.db][(app_label, model)]
        except KeyError:
            ct = self.get(app_label=app_label, model=model)
            self._add_to_cache(self.db, ct)
        return ct