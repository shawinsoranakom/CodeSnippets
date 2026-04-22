def _random_row(self) -> List[int]:
        row: List[int] = []
        for _ in range(0, self._num_of_cols):
            row.append(random.randint(1, 1000000))
        return row