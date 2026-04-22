def toPandas(self):
        self._lazy_evaluation()
        if self._limit > 0:
            return self._data.head(self._limit)
        return self._data