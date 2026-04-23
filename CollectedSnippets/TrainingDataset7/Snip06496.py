def _get_from_cache(self, opts):
        key = (opts.app_label, opts.model_name)
        return self._cache[self.db][key]