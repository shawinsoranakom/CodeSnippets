def get_context(self, name, value, attrs=None):
        attrs = {} if attrs is None else attrs
        context = super().get_context(name, value, attrs)
        if self.is_localized:
            self.widget.is_localized = self.is_localized
        value = value or []
        context["widget"]["subwidgets"] = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get("id")
        for i in range(max(len(value), self.size)):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = {**final_attrs, "id": "%s_%s" % (id_, i)}
            context["widget"]["subwidgets"].append(
                self.widget.get_context(name + "_%s" % i, widget_value, final_attrs)[
                    "widget"
                ]
            )
        return context