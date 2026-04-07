def __iter__(self):
        for field in self.fields:
            yield Fieldline(
                self.form, field, self.readonly_fields, model_admin=self.model_admin
            )