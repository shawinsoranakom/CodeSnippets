def sort_dependencies(app_list, allow_cycles=False):
    """Sort a list of (app_config, models) pairs into a single list of models.

    The single list of models is sorted so that any model with a natural key
    is serialized before a normal model, and any model with a natural key
    dependency has it's dependencies serialized first.

    If allow_cycles is True, return the best-effort ordering that will respect
    most of dependencies but ignore some of them to break the cycles.
    """
    # Process the list of models, and get the list of dependencies
    model_dependencies = []
    models = set()
    for app_config, model_list in app_list:
        if model_list is None:
            model_list = app_config.get_models()

        for model in model_list:
            models.add(model)
            # Add any explicitly defined dependencies
            if hasattr(model, "natural_key"):
                deps = getattr(model.natural_key, "dependencies", [])
                if deps:
                    deps = [apps.get_model(dep) for dep in deps]
            else:
                deps = []

            # Now add a dependency for any FK relation with a model that
            # defines a natural key
            for field in model._meta.fields:
                if field.remote_field:
                    rel_model = field.remote_field.model
                    if hasattr(rel_model, "natural_key") and rel_model != model:
                        deps.append(rel_model)
            # Also add a dependency for any simple M2M relation with a model
            # that defines a natural key. M2M relations with explicit through
            # models don't count as dependencies.
            for field in model._meta.many_to_many:
                if field.remote_field.through._meta.auto_created:
                    rel_model = field.remote_field.model
                    if hasattr(rel_model, "natural_key") and rel_model != model:
                        deps.append(rel_model)
            model_dependencies.append((model, deps))

    model_dependencies.reverse()
    # Now sort the models to ensure that dependencies are met. This
    # is done by repeatedly iterating over the input list of models.
    # If all the dependencies of a given model are in the final list,
    # that model is promoted to the end of the final list. This process
    # continues until the input list is empty, or we do a full iteration
    # over the input models without promoting a model to the final list.
    # If we do a full iteration without a promotion, that means there are
    # circular dependencies in the list.
    model_list = []
    while model_dependencies:
        skipped = []
        changed = False
        while model_dependencies:
            model, deps = model_dependencies.pop()

            # If all of the models in the dependency list are either already
            # on the final model list, or not on the original serialization
            # list, then we've found another model with all it's dependencies
            # satisfied.
            if all(d not in models or d in model_list for d in deps):
                model_list.append(model)
                changed = True
            else:
                skipped.append((model, deps))
        if not changed:
            if allow_cycles:
                # If cycles are allowed, add the last skipped model and ignore
                # its dependencies. This could be improved by some graph
                # analysis to ignore as few dependencies as possible.
                model, _ = skipped.pop()
                model_list.append(model)
            else:
                raise RuntimeError(
                    "Can't resolve dependencies for %s in serialized app list."
                    % ", ".join(
                        model._meta.label
                        for model, deps in sorted(
                            skipped, key=lambda obj: obj[0].__name__
                        )
                    ),
                )
        model_dependencies = skipped

    return model_list