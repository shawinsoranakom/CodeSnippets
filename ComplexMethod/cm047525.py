def _init_model_class_attributes(model_cls: type[BaseModel]):
    """ Initialize model class attributes. """
    assert is_model_class(model_cls)

    model_cls._description = model_cls._name
    model_cls._table = model_cls._name.replace('.', '_')
    model_cls._log_access = model_cls._auto
    inherits = {}
    depends = {}

    for base in reversed(model_cls._base_classes__):
        if is_model_definition(base):
            # the following attributes are not taken from registry classes
            if model_cls._name not in base._inherit and not base._description:
                _logger.warning("The model %s has no _description", model_cls._name)
            model_cls._description = base._description or model_cls._description
            model_cls._table = base._table or model_cls._table
            model_cls._log_access = getattr(base, '_log_access', model_cls._log_access)

        inherits.update(base._inherits)

        for mname, fnames in base._depends.items():
            depends.setdefault(mname, []).extend(fnames)

    # avoid assigning an empty dict to save memory
    if inherits:
        model_cls._inherits = inherits
    if depends:
        model_cls._depends = depends

    # update _inherits_children of parent models
    registry = model_cls.pool
    for parent_name in model_cls._inherits:
        registry[parent_name]._inherits_children.add(model_cls._name)

    # recompute attributes of _inherit_children models
    for child_name in model_cls._inherit_children:
        _init_model_class_attributes(registry[child_name])