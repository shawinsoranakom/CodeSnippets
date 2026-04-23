def PROTECT(collector, field, sub_objs, using):
    raise ProtectedError(
        "Cannot delete some instances of model '%s' because they are "
        "referenced through a protected foreign key: '%s.%s'"
        % (
            field.remote_field.model.__name__,
            sub_objs[0].__class__.__name__,
            field.name,
        ),
        sub_objs,
    )