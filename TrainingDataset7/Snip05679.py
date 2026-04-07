def __init__(
        self,
        formset,
        form,
        fieldsets,
        prepopulated_fields,
        original,
        readonly_fields=None,
        model_admin=None,
        view_on_site_url=None,
    ):
        self.formset = formset
        self.model_admin = model_admin
        self.original = original
        self.show_url = original and view_on_site_url is not None
        self.absolute_url = view_on_site_url
        super().__init__(
            form, fieldsets, prepopulated_fields, readonly_fields, model_admin
        )