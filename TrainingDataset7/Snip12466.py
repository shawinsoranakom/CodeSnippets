def get_bound_field(self, form, field_name):
        """
        Return a BoundField instance that will be used when accessing the form
        field in a template.
        """
        bound_field_class = (
            self.bound_field_class or form.bound_field_class or BoundField
        )
        return bound_field_class(form, self, field_name)