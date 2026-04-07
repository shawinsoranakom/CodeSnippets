def build_instance(Model, data, db):
    """
    Build a model instance.

    If the model instance doesn't have a primary key and the model supports
    natural keys, try to retrieve it from the database.
    """
    default_manager = Model._meta.default_manager
    pk = data.get(Model._meta.pk.attname)
    if (
        pk is None
        and hasattr(default_manager, "get_by_natural_key")
        and hasattr(Model, "natural_key")
    ):
        obj = Model(**data)
        obj._state.db = db
        natural_key = obj.natural_key()
        try:
            data[Model._meta.pk.attname] = Model._meta.pk.to_python(
                default_manager.db_manager(db).get_by_natural_key(*natural_key).pk
            )
        except Model.DoesNotExist:
            pass
    return Model(**data)