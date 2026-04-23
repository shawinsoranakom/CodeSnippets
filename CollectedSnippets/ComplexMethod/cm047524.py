def add_to_registry(registry: Registry, model_def: type[BaseModel]) -> type[BaseModel]:
    """ Add a model definition to the given registry, and return its
    corresponding model class.  This function creates or extends a model class
    for the given model definition.
    """
    assert is_model_definition(model_def)

    if hasattr(model_def, '_constraints'):
        _logger.warning("Model attribute '_constraints' is no longer supported, "
                        "please use @api.constrains on methods instead.")
    if hasattr(model_def, '_sql_constraints'):
        _logger.warning("Model attribute '_sql_constraints' is no longer supported, "
                        "please define models.Constraint on the model.")

    # all models except 'base' implicitly inherit from 'base'
    name = model_def._name
    parent_names = list(model_def._inherit)
    if name != 'base':
        parent_names.append('base')

    # create or retrieve the model's class
    if name in parent_names:
        if name not in registry:
            raise TypeError(f"Model {name!r} does not exist in registry.")
        model_cls = registry[name]
        _check_model_extension(model_cls, model_def)
    else:
        model_cls = type(name, (model_def,), {
            'pool': registry,                       # this makes it a model class
            '_name': name,
            '_register': False,
            '_original_module': model_def._module,
            '_inherit_module': {},                  # map parent to introducing module
            '_inherit_children': OrderedSet(),      # names of children models
            '_inherits_children': set(),            # names of children models
            '_fields__': {},                        # populated in _setup()
            '_table_objects': frozendict(),         # populated in _setup()
        })
        model_cls._fields = MappingProxyType(model_cls._fields__)

    # determine all the classes the model should inherit from
    bases = LastOrderedSet([model_def])
    for parent_name in parent_names:
        if parent_name not in registry:
            raise TypeError(f"Model {name!r} inherits from non-existing model {parent_name!r}.")
        parent_cls = registry[parent_name]
        if parent_name == name:
            for base in parent_cls._base_classes__:
                bases.add(base)
        else:
            _check_model_parent_extension(model_cls, model_def, parent_cls)
            bases.add(parent_cls)
            model_cls._inherit_module[parent_name] = model_def._module
            parent_cls._inherit_children.add(name)

    # model_cls.__bases__ must be assigned those classes; however, this
    # operation is quite slow, so we do it once in method _prepare_setup()
    model_cls._base_classes__ = tuple(bases)

    # determine the attributes of the model's class
    _init_model_class_attributes(model_cls)

    check_pg_name(model_cls._table)

    # Transience
    if model_cls._transient and not model_cls._log_access:
        raise TypeError(
            "TransientModels must have log_access turned on, "
            "in order to implement their vacuum policy"
        )

    # update the registry after all checks have passed
    registry[name] = model_cls

    # mark all impacted models for setup
    for model_name in registry.descendants([name], '_inherit', '_inherits'):
        registry[model_name]._setup_done__ = False

    return model_cls