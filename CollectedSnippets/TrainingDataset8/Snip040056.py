def collect(self) -> List[List[int]]:
        """Returns fake Data like, which imitates collection of snowflake.snowpark.dataframe.DataFrame"""
        self._lazy_evaluation()
        return self._data