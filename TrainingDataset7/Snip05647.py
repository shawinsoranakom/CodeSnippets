def __init__(
        self,
        form,
        fieldsets,
        prepopulated_fields,
        readonly_fields=None,
        model_admin=None,
    ):
        self.form, self.fieldsets = form, fieldsets
        self.prepopulated_fields = [
            {"field": form[field_name], "dependencies": [form[f] for f in dependencies]}
            for field_name, dependencies in prepopulated_fields.items()
        ]
        self.model_admin = model_admin
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields