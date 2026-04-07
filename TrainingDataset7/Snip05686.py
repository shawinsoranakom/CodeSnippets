def __iter__(self):
        fk = getattr(self.formset, "fk", None)
        for field in self.fields:
            if not fk or fk.name != field:
                yield Fieldline(
                    self.form, field, self.readonly_fields, model_admin=self.model_admin
                )