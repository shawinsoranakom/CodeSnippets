def check_generic_foreign_keys(app_configs, **kwargs):
    from .fields import GenericForeignKeyDescriptor

    if app_configs is None:
        models = apps.get_models()
    else:
        models = chain.from_iterable(
            app_config.get_models() for app_config in app_configs
        )
    errors = []
    descriptors = (
        obj
        for model in models
        for obj in vars(model).values()
        if isinstance(obj, GenericForeignKeyDescriptor)
    )
    for descriptor in descriptors:
        errors.extend(descriptor.field.check())
    return errors