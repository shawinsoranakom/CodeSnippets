def deserialize(
        self,
        ui_value: Optional[List[int]],
        widget_id: str = "",
    ) -> List[T]:
        current_value: List[int] = (
            ui_value if ui_value is not None else self.default_value
        )
        return [self.options[i] for i in current_value]