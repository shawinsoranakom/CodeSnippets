def __post_init__(self) -> None:
        if self.min > self.max:
            raise StreamlitAPIException(
                f"The `min_value`, set to {self.min}, shouldn't be larger "
                f"than the `max_value`, set to {self.max}."
            )

        if self.value:
            start_value = self.value[0]
            end_value = self.value[-1]

            if (start_value < self.min) or (end_value > self.max):
                raise StreamlitAPIException(
                    f"The default `value` of {self.value} "
                    f"must lie between the `min_value` of {self.min} "
                    f"and the `max_value` of {self.max}, inclusively."
                )