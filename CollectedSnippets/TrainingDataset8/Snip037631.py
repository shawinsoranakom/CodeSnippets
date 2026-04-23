def deserialize(
        self,
        ui_value: Any,
        widget_id: str = "",
    ) -> DateWidgetReturn:
        return_value: Sequence[date]
        if ui_value is not None:
            return_value = tuple(
                datetime.strptime(v, "%Y/%m/%d").date() for v in ui_value
            )
        else:
            return_value = self.value.value

        if not self.value.is_range:
            return return_value[0]
        return cast(DateWidgetReturn, tuple(return_value))