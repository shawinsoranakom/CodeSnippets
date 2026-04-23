def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list/tuple of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, (list, tuple)):
            value = self.decompress(value)

        final_attrs = context["widget"]["attrs"]
        input_type = final_attrs.pop("type", None)
        id_ = final_attrs.get("id")
        subwidgets = []
        for i, (widget_name, widget) in enumerate(
            zip(self.widgets_names, self.widgets)
        ):
            if input_type is not None:
                widget.input_type = input_type
            widget_name = name + widget_name
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                widget_attrs = final_attrs.copy()
                widget_attrs["id"] = "%s_%s" % (id_, i)
            else:
                widget_attrs = final_attrs
            subwidgets.append(
                widget.get_context(widget_name, widget_value, widget_attrs)["widget"]
            )
        context["widget"]["subwidgets"] = subwidgets
        return context