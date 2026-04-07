def formfield(self, **kwargs):
        if self.choices is not None:
            include_blank = not (self.has_default() or "initial" in kwargs)
            defaults = {"choices": self.get_choices(include_blank=include_blank)}
        else:
            form_class = forms.NullBooleanField if self.null else forms.BooleanField
            # In HTML checkboxes, 'required' means "must be checked" which is
            # different from the choices case ("must select some value").
            # required=False allows unchecked checkboxes.
            defaults = {"form_class": form_class, "required": False}
        return super().formfield(**{**defaults, **kwargs})