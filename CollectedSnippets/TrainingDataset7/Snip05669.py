def __init__(
        self,
        inline,
        formset,
        fieldsets,
        prepopulated_fields=None,
        readonly_fields=None,
        model_admin=None,
        has_add_permission=True,
        has_change_permission=True,
        has_delete_permission=True,
        has_view_permission=True,
    ):
        self.opts = inline
        self.formset = formset
        self.fieldsets = fieldsets
        self.model_admin = model_admin
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields
        if prepopulated_fields is None:
            prepopulated_fields = {}
        self.prepopulated_fields = prepopulated_fields
        self.classes = " ".join(inline.classes) if inline.classes else ""
        self.has_add_permission = has_add_permission
        self.has_change_permission = has_change_permission
        self.has_delete_permission = has_delete_permission
        self.has_view_permission = has_view_permission