def _construct_form(self, i, **kwargs):
        """Instantiate and return the i-th form instance in a formset."""
        defaults = {
            "auto_id": self.auto_id,
            "prefix": self.add_prefix(i),
            "error_class": self.error_class,
            # Don't render the HTML 'required' attribute as it may cause
            # incorrect validation for extra, optional, and deleted
            # forms in the formset.
            "use_required_attribute": False,
            "renderer": self.form_renderer,
        }
        if self.is_bound:
            defaults["data"] = self.data
            defaults["files"] = self.files
        if self.initial and "initial" not in kwargs:
            try:
                defaults["initial"] = self.initial[i]
            except IndexError:
                pass
        # Allow extra forms to be empty, unless they're part of
        # the minimum forms.
        if i >= self.initial_form_count() and i >= self.min_num:
            defaults["empty_permitted"] = True
        defaults.update(kwargs)
        form = self.form(**defaults)
        self.add_fields(form, i)
        return form