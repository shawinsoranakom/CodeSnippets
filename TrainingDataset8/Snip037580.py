def deserialize(
        self,
        ui_value: Optional[int],
        widget_id: str = "",
    ) -> Optional[T]:
        idx = ui_value if ui_value is not None else self.index

        return (
            self.options[idx]
            if len(self.options) > 0 and self.options[idx] is not None
            else None
        )