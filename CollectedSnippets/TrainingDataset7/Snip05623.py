def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = "%s__exact" % field_path
        self.lookup_kwarg2 = "%s__isnull" % field_path
        self.lookup_val = get_last_value_from_parameters(params, self.lookup_kwarg)
        self.lookup_val2 = get_last_value_from_parameters(params, self.lookup_kwarg2)
        super().__init__(field, request, params, model, model_admin, field_path)
        if (
            self.used_parameters
            and self.lookup_kwarg in self.used_parameters
            and self.used_parameters[self.lookup_kwarg] in ("1", "0")
        ):
            self.used_parameters[self.lookup_kwarg] = bool(
                int(self.used_parameters[self.lookup_kwarg])
            )