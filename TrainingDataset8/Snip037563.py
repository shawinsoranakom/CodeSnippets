def deserialize(self, ui_value: Optional[Number], widget_id: str = "") -> Number:
        if ui_value is not None:
            val = ui_value
        else:
            # Widget has not been used; fallback to the original value,
            val = self.value

        if self.data_type == NumberInputProto.INT:
            val = int(val)

        return val