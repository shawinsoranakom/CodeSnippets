def annotation_select(self):
        """
        Return the dictionary of aggregate columns that are not masked and
        should be used in the SELECT clause. Cache this result for performance.
        """
        if self._annotation_select_cache is not None:
            return self._annotation_select_cache
        elif not self.annotations:
            return {}
        elif self.annotation_select_mask is not None:
            self._annotation_select_cache = {
                k: v
                for k, v in self.annotations.items()
                if k in self.annotation_select_mask
            }
            return self._annotation_select_cache
        else:
            return self.annotations