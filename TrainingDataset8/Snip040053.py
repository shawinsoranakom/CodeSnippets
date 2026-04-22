def __init__(
        self, is_map: bool = False, num_of_rows: int = 50000, num_of_cols: int = 4
    ):
        self._data = None
        self._is_map = is_map
        self._num_of_rows = num_of_rows
        self._num_of_cols = num_of_cols