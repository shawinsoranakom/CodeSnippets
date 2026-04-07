def must_inherit_from(parent, option, obj, id):
    return [
        checks.Error(
            "The value of '%s' must inherit from '%s'." % (option, parent),
            obj=obj.__class__,
            id=id,
        ),
    ]