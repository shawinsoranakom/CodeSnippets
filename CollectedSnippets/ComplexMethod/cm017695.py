def label_tag(self, contents=None, attrs=None, label_suffix=None, tag=None):
        """
        Wrap the given contents in a <label>, if the field has an ID attribute.
        contents should be mark_safe'd to avoid HTML escaping. If contents
        aren't given, use the field's HTML-escaped label.

        If attrs are given, use them as HTML attributes on the <label> tag.

        label_suffix overrides the form's label_suffix.
        """
        contents = contents or self.label
        if label_suffix is None:
            label_suffix = (
                self.field.label_suffix
                if self.field.label_suffix is not None
                else self.form.label_suffix
            )
        # Only add the suffix if the label does not end in punctuation.
        # Translators: If found as last label character, these punctuation
        # characters will prevent the default label_suffix to be appended to
        # the label
        if label_suffix and contents and contents[-1] not in _(":?.!"):
            contents = format_html("{}{}", contents, label_suffix)
        widget = self.field.widget
        id_ = widget.attrs.get("id") or self.auto_id
        if id_:
            id_for_label = widget.id_for_label(id_)
            if id_for_label:
                attrs = attrs or {}
                if tag != "legend":
                    attrs = {**attrs, "for": id_for_label}
            if self.field.required and hasattr(self.form, "required_css_class"):
                attrs = attrs or {}
                if "class" in attrs:
                    attrs["class"] += " " + self.form.required_css_class
                else:
                    attrs["class"] = self.form.required_css_class
        context = {
            "field": self,
            "label": contents,
            "attrs": attrs,
            "use_tag": bool(id_),
            "tag": tag or "label",
        }
        return self.form.render(self.form.template_name_label, context)