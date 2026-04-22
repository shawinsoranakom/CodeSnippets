def serialize(self, value: List[T]) -> List[int]:
        return _check_and_convert_to_indices(self.options, value)