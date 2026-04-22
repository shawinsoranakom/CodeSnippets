def deserialize(
        self,
        ui_value: Optional[List[int]],
        widget_id: str = "",
    ) -> Union[T, Tuple[T, T]]:
        if not ui_value:
            # Widget has not been used; fallback to the original value,
            ui_value = self.value

        # The widget always returns floats, so convert to ints before indexing
        return_value: Tuple[T, T] = cast(
            Tuple[T, T],
            tuple(map(lambda x: self.options[int(x)], ui_value)),
        )

        # If the original value was a list/tuple, so will be the output (and vice versa)
        return return_value if self.is_range_value else return_value[0]