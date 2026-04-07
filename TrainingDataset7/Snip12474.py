def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, NumberInput):
            if self.min_value is not None:
                attrs["min"] = self.min_value
            if self.max_value is not None:
                attrs["max"] = self.max_value
            if self.step_size is not None:
                attrs["step"] = self.step_size
        return attrs