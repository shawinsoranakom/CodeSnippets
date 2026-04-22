def deserialize(self, ui_value: Optional[bool], widget_id: str = "") -> bool:
        return bool(ui_value if ui_value is not None else self.value)