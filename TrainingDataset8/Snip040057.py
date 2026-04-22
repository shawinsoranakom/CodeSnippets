def _lazy_evaluation(self):
        """Sometimes we don't need data inside Data like class, so we populate it once and only when necessary"""
        if self._data is None:
            if self._is_map:
                self._data = pd.DataFrame(
                    (
                        np.random.randn(self._num_of_rows, 2) / [50, 50]
                        + [37.76, -122.4]
                    ),
                    columns=["lat", "lon"],
                )
            else:
                random.seed(0)
                self._data = self._random_data()