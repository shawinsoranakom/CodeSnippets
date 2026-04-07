def create(cls, field, request, params, model, model_admin, field_path):
        for test, list_filter_class in cls._field_list_filters:
            if test(field):
                return list_filter_class(
                    field, request, params, model, model_admin, field_path=field_path
                )