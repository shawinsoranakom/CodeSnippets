def get_queryset(self):
            if (cache := self.get_prefetch_cache()) is not None:
                return cache
            else:
                queryset = super().get_queryset()
                return self._apply_rel_filters(queryset)