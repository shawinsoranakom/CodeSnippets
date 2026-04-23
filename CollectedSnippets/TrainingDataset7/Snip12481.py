def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, NumberInput) and "step" not in widget.attrs:
            if self.decimal_places is not None:
                # Use exponential notation for small values since they might
                # be parsed as 0 otherwise. ref #20765
                step = str(Decimal(1).scaleb(-self.decimal_places)).lower()
            else:
                step = "any"
            attrs.setdefault("step", step)
        return attrs