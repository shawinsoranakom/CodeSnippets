def label_tag(self):
        attrs = {}
        if not self.is_first:
            attrs["class"] = "inline"
        label = self.field["label"]
        return format_html(
            "<label{}>{}{}</label>",
            flatatt(attrs),
            capfirst(label),
            self.form.label_suffix,
        )