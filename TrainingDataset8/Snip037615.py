def deserialize(self, ui_value: Optional[str], widget_id: str = "") -> str:
        return str(ui_value if ui_value is not None else self.value)