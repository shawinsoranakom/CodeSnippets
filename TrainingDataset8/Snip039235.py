def _lazy_evaluation(self):
        if self._data is not None:
            return
        if self._is_map:
            self._data = pd.DataFrame(MAP_DATA, columns=["lat", "lon"])
            return
        if self._is_numpy_arr:
            self._data = pd.DataFrame(
                np.random.randn(self._num_of_rows, 4), columns=["A", "B", "C", "D"]
            )
            return
        self._data = pd.DataFrame(
            PERSONAL_DATA,
        )