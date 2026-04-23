def _setup(model_cls: type[BaseModel], env: Environment):
    """ Determine all the fields of the model. """
    if model_cls._setup_done__:
        return

    # the classes that define this model, i.e., the ones that are not
    # registry classes; the purpose of this attribute is to behave as a
    # cache of [c for c in model_cls.mro() if not is_model_class(c))], which
    # is heavily used in function fields.resolve_mro()
    model_cls._model_classes__ = tuple(c for c in model_cls.mro() if getattr(c, 'pool', None) is None)

    # 1. determine the proper fields of the model: the fields defined on the
    # class and magic fields, not the inherited or custom ones

    # retrieve fields from parent classes, and duplicate them on model_cls to
    # avoid clashes with inheritance between different models
    for name in model_cls._fields:
        discardattr(model_cls, name)
    model_cls._fields__.clear()

    # collect the definitions of each field (base definition + overrides)
    definitions = defaultdict(list)
    for cls in reversed(model_cls._model_classes__):
        # this condition is an optimization of is_model_definition(cls)
        if isinstance(cls, models.MetaModel):
            for field in cls._field_definitions:
                definitions[field.name].append(field)

    for name, fields_ in definitions.items():
        if f'{model_cls._name}.{name}' in model_cls.pool._database_translated_fields:
            # the field is currently translated in the database; ensure the
            # field is translated to avoid converting its column to varchar
            # and losing data
            translate = next((
                field._args__['translate'] for field in reversed(fields_) if 'translate' in field._args__
            ), False)
            if not translate:
                field_translate = FIELD_TRANSLATE.get(
                    model_cls.pool._database_translated_fields[f'{model_cls._name}.{name}'],
                    True
                )
                # patch the field definition by adding an override
                _logger.debug("Patching %s.%s with translate=True", model_cls._name, name)
                fields_.append(type(fields_[0])(translate=field_translate))
        if f'{model_cls._name}.{name}' in model_cls.pool._database_company_dependent_fields:
            # the field is currently company dependent in the database; ensure
            # the field is company dependent to avoid converting its column to
            # the base data type
            company_dependent = next((
                field._args__['company_dependent'] for field in reversed(fields_) if 'company_dependent' in field._args__
            ), False)
            if not company_dependent:
                # validate column type again in case the column type is changed by upgrade script
                rows = env.execute_query(sql.SQL(
                    'SELECT data_type FROM information_schema.columns'
                    ' WHERE table_name = %s AND column_name = %s AND table_schema = current_schema',
                    model_cls._table, name,
                ))
                if rows and rows[0][0] == 'jsonb':
                    # patch the field definition by adding an override
                    _logger.debug("Patching %s.%s with company_dependent=True", model_cls._name, name)
                    fields_.append(type(fields_[0])(company_dependent=True))
        if len(fields_) == 1 and fields_[0]._direct and fields_[0].model_name == model_cls._name:
            model_cls._fields__[name] = fields_[0]
        else:
            Field = type(fields_[-1])
            add_field(model_cls, name, Field(_base_fields__=tuple(fields_)))

    # 2. add manual fields
    if model_cls.pool._init_modules:
        _add_manual_fields(model_cls, env)

    # 3. make sure that parent models determine their own fields, then add
    # inherited fields to model_cls
    _check_inherits(model_cls)
    for parent_name in model_cls._inherits:
        _setup(model_cls.pool[parent_name], env)
    _add_inherited_fields(model_cls)

    # 4. initialize more field metadata
    model_cls._setup_done__ = True

    for field in model_cls._fields.values():
        field.prepare_setup()

    # 5. determine and validate rec_name
    if model_cls._rec_name:
        assert model_cls._rec_name in model_cls._fields, \
            "Invalid _rec_name=%r for model %r" % (model_cls._rec_name, model_cls._name)
    elif 'name' in model_cls._fields:
        model_cls._rec_name = 'name'
    elif model_cls._custom and 'x_name' in model_cls._fields:
        model_cls._rec_name = 'x_name'

    # 6. determine and validate active_name
    if model_cls._active_name:
        assert (model_cls._active_name in model_cls._fields
                and model_cls._active_name in ('active', 'x_active')), \
            ("Invalid _active_name=%r for model %r; only 'active' and "
            "'x_active' are supported and the field must be present on "
            "the model") % (model_cls._active_name, model_cls._name)
    elif 'active' in model_cls._fields:
        model_cls._active_name = 'active'
    elif 'x_active' in model_cls._fields:
        model_cls._active_name = 'x_active'

    # 7. determine table objects
    assert not model_cls._table_object_definitions, "model_cls is a registry model"
    model_cls._table_objects = frozendict({
        cons.full_name(model_cls): cons
        for cls in reversed(model_cls._model_classes__)
        if isinstance(cls, models.MetaModel)
        for cons in cls._table_object_definitions
    })