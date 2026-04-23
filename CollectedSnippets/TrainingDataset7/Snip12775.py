def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        final_attrs = context["widget"]["attrs"]
        id_ = context["widget"]["attrs"].get("id")

        subwidgets = []
        for index, value_ in enumerate(context["widget"]["value"]):
            widget_attrs = final_attrs.copy()
            if id_:
                # An ID attribute was given. Add a numeric index as a suffix
                # so that the inputs don't all have the same ID attribute.
                widget_attrs["id"] = "%s_%s" % (id_, index)
            widget = HiddenInput()
            widget.is_required = self.is_required
            subwidgets.append(widget.get_context(name, value_, widget_attrs)["widget"])

        context["widget"]["subwidgets"] = subwidgets
        return context