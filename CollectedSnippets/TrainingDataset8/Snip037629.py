def deserialize(self, ui_value: Optional[str], widget_id: Any = "") -> time:
        return (
            datetime.strptime(ui_value, "%H:%M").time()
            if ui_value is not None
            else self.value
        )