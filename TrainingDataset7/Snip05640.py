def __init__(self, field, request, params, model, model_admin, field_path):
        if not field.empty_strings_allowed and not field.null:
            raise ImproperlyConfigured(
                "The list filter '%s' cannot be used with field '%s' which "
                "doesn't allow empty strings and nulls."
                % (
                    self.__class__.__name__,
                    field.name,
                )
            )
        self.lookup_kwarg = "%s__isempty" % field_path
        self.lookup_val = get_last_value_from_parameters(params, self.lookup_kwarg)
        super().__init__(field, request, params, model, model_admin, field_path)