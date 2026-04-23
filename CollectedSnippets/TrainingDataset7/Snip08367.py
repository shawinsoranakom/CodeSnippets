def field_error(model_key, func, args, keywords):
        error_msg = (
            "The field %(field)s was declared with a lazy reference "
            "to '%(model)s', but %(model_error)s."
        )
        params = {
            "model": ".".join(model_key),
            "field": keywords["field"],
            "model_error": app_model_error(model_key),
        }
        return Error(error_msg % params, obj=keywords["field"], id="fields.E307")