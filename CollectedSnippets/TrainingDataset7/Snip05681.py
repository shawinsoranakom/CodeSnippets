def needs_explicit_pk_field(self):
        return (
            # Auto fields are editable, so check for auto or non-editable pk.
            self.form._meta.model._meta.auto_field
            or not self.form._meta.model._meta.pk.editable
            # The pk can be editable, but excluded from the inline.
            or (
                self.form._meta.exclude
                and self.form._meta.model._meta.pk.name in self.form._meta.exclude
            )
            or
            # Also search any parents for an auto field. (The pk info is
            # propagated to child models so that does not need to be checked
            # in parents.)
            any(
                parent._meta.auto_field or not parent._meta.model._meta.pk.editable
                for parent in self.form._meta.model._meta.all_parents
            )
        )