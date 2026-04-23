def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = "%s__in" % field_path
        super().__init__(field, request, params, model, model_admin, field_path)