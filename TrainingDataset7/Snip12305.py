def extra_select(self):
        if self._extra_select_cache is not None:
            return self._extra_select_cache
        if not self.extra:
            return {}
        elif self.extra_select_mask is not None:
            self._extra_select_cache = {
                k: v for k, v in self.extra.items() if k in self.extra_select_mask
            }
            return self._extra_select_cache
        else:
            return self.extra