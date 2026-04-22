def deserialize(
        self,
        ui_value: Optional[int],
        widget_id: str = "",
    ) -> Optional[T]:
        idx: int = ui_value if ui_value is not None else self.index

        return self.options[idx] if len(self.options) > 0 else None