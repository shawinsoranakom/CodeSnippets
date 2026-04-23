def take(self, n: int):
        """Returns n element of fake Data like, which imitates take of snowflake.snowpark.dataframe.DataFrame"""
        self._lazy_evaluation()
        if n > self._num_of_rows:
            n = self._num_of_rows
        return self._data[:n]