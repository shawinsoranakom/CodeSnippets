def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, FileInput) and "accept" not in widget.attrs:
            attrs.setdefault("accept", "image/*")
        return attrs