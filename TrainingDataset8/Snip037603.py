def deserialize(self, ui_value: Optional[List[float]], widget_id: str = ""):
        if ui_value is not None:
            val: Any = ui_value
        else:
            # Widget has not been used; fallback to the original value,
            val = self.value

        # The widget always returns a float array, so fix the return type if necessary
        if self.data_type == SliderProto.INT:
            val = [int(v) for v in val]
        if self.data_type == SliderProto.DATETIME:
            val = [_micros_to_datetime(int(v), self.orig_tz) for v in val]
        if self.data_type == SliderProto.DATE:
            val = [_micros_to_datetime(int(v), self.orig_tz).date() for v in val]
        if self.data_type == SliderProto.TIME:
            val = [
                _micros_to_datetime(int(v), self.orig_tz)
                .time()
                .replace(tzinfo=self.orig_tz)
                for v in val
            ]
        return val[0] if self.single_value else tuple(val)