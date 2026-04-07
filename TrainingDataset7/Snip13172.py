def find_partial_source(self, full_source):
        if (
            self._source_start is not None
            and self._source_end is not None
            and 0 <= self._source_start <= self._source_end <= len(full_source)
        ):
            return full_source[self._source_start : self._source_end]

        return ""