def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.max_length is not None and not widget.is_hidden:
            # The HTML attribute is maxlength, not max_length.
            attrs["maxlength"] = str(self.max_length)
        if self.min_length is not None and not widget.is_hidden:
            # The HTML attribute is minlength, not min_length.
            attrs["minlength"] = str(self.min_length)
        return attrs