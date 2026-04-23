def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = "%s__exact" % field_path
        self.lookup_kwarg_isnull = "%s__isnull" % field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val_isnull = get_last_value_from_parameters(
            params, self.lookup_kwarg_isnull
        )
        super().__init__(field, request, params, model, model_admin, field_path)