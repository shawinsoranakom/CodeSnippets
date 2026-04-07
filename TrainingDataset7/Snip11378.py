def lazy_related_operation(function, model, *related_models, **kwargs):
    """
    Schedule `function` to be called once `model` and all `related_models`
    have been imported and registered with the app registry. `function` will
    be called with the newly-loaded model classes as its positional arguments,
    plus any optional keyword arguments.

    The `model` argument must be a model class. Each subsequent positional
    argument is another model, or a reference to another model - see
    `resolve_relation()` for the various forms these may take. Any relative
    references will be resolved relative to `model`.

    This is a convenience wrapper for `Apps.lazy_model_operation` - the app
    registry model used is the one found in `model._meta.apps`.
    """
    models = [model] + [resolve_relation(model, rel) for rel in related_models]
    model_keys = (make_model_tuple(m) for m in models)
    apps = model._meta.apps
    return apps.lazy_model_operation(partial(function, **kwargs), *model_keys)