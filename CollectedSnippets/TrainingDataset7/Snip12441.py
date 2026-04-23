def legend_tag(self, contents=None, attrs=None, label_suffix=None):
        """
        Wrap the given contents in a <legend>, if the field has an ID
        attribute. Contents should be mark_safe'd to avoid HTML escaping. If
        contents aren't given, use the field's HTML-escaped label.

        If attrs are given, use them as HTML attributes on the <legend> tag.

        label_suffix overrides the form's label_suffix.
        """
        return self.label_tag(contents, attrs, label_suffix, tag="legend")