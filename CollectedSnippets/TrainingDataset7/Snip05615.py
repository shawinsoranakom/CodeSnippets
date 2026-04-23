def __init__(self, field, request, params, model, model_admin, field_path):
        other_model = get_model_from_relation(field)
        self.lookup_kwarg = "%s__%s__exact" % (field_path, field.target_field.name)
        self.lookup_kwarg_isnull = "%s__isnull" % field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val_isnull = get_last_value_from_parameters(
            params, self.lookup_kwarg_isnull
        )
        super().__init__(field, request, params, model, model_admin, field_path)
        self.lookup_choices = self.field_choices(field, request, model_admin)
        if hasattr(field, "verbose_name"):
            self.lookup_title = field.verbose_name
        else:
            self.lookup_title = other_model._meta.verbose_name
        self.title = self.lookup_title
        self.empty_value_display = model_admin.get_empty_value_display()