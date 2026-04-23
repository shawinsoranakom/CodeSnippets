def __iter__(self):
        for name, options in self.fieldsets:
            yield InlineFieldset(
                self.formset,
                self.form,
                name,
                self.readonly_fields,
                model_admin=self.model_admin,
                **options,
            )