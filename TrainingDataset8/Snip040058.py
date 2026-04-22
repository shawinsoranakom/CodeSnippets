def _random_data(self) -> List[List[int]]:
        data: List[List[int]] = []
        for _ in range(0, self._num_of_rows):
            data.append(self._random_row())
        return data