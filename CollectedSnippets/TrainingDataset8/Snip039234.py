def __init__(
        self, is_map: bool = False, is_numpy_arr: bool = False, num_of_rows: int = 50000
    ):
        self._data = None
        self._is_map: bool = is_map
        self._num_of_rows: int = num_of_rows
        self._is_numpy_arr: bool = is_numpy_arr
        self._limit: int = 0