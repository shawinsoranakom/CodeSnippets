def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, NumberInput) and "step" not in widget.attrs:
            if self.step_size is not None:
                step = str(self.step_size)
            else:
                step = "any"
            attrs.setdefault("step", step)
        return attrs