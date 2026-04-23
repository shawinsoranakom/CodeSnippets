def label_tag(self):
        classes = []
        contents = conditional_escape(self.field.label)
        if self.is_checkbox:
            classes.append("vCheckboxLabel")

        if self.field.field.required:
            classes.append("required")
        if not self.is_first:
            classes.append("inline")
        attrs = {"class": " ".join(classes)} if classes else {}
        tag = "legend" if self.is_fieldset else None
        # checkboxes should not have a label suffix as the checkbox appears
        # to the left of the label.
        return self.field.label_tag(
            contents=mark_safe(contents),
            attrs=attrs,
            label_suffix="" if self.is_checkbox else None,
            tag=tag,
        )