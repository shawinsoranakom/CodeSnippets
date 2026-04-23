def get_related_models_recursive(model):
    """
    Return all models that have a direct or indirect relationship
    to the given model.

    Relationships are either defined by explicit relational fields, like
    ForeignKey, ManyToManyField or OneToOneField, or by inheriting from another
    model (a superclass is related to its subclasses, but not vice versa).
    Note, however, that a model inheriting from a concrete model is also
    related to its superclass through the implicit *_ptr OneToOneField on the
    subclass.
    """
    seen = set()
    queue = _get_related_models(model)
    for rel_mod in queue:
        rel_app_label, rel_model_name = (
            rel_mod._meta.app_label,
            rel_mod._meta.model_name,
        )
        if (rel_app_label, rel_model_name) in seen:
            continue
        seen.add((rel_app_label, rel_model_name))
        queue.extend(_get_related_models(rel_mod))
    return seen - {(model._meta.app_label, model._meta.model_name)}