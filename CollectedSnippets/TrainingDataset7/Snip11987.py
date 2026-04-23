def raw(self, raw_query, params=(), translations=None, using=None):
        if using is None:
            using = self.db
        qs = RawQuerySet(
            raw_query,
            model=self.model,
            params=params,
            translations=translations,
            using=using,
            fetch_mode=self._fetch_mode,
        )
        qs._prefetch_related_lookups = self._prefetch_related_lookups[:]
        return qs