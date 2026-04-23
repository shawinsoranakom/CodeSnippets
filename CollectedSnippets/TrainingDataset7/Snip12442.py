def css_classes(self, extra_classes=None):
        """
        Return a string of space-separated CSS classes for this field.
        """
        if hasattr(extra_classes, "split"):
            extra_classes = extra_classes.split()
        extra_classes = set(extra_classes or [])
        if self.errors and hasattr(self.form, "error_css_class"):
            extra_classes.add(self.form.error_css_class)
        if self.field.required and hasattr(self.form, "required_css_class"):
            extra_classes.add(self.form.required_css_class)
        return " ".join(extra_classes)