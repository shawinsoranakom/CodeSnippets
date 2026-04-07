def refer_to_missing_field(field, option, obj, id):
    return [
        checks.Error(
            "The value of '%s' refers to '%s', which is not a field of '%s'."
            % (option, field, obj.model._meta.label),
            obj=obj.__class__,
            id=id,
        ),
    ]