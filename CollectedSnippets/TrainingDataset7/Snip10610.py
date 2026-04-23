def from_db(cls, db, field_names, values, *, fetch_mode=None):
        if len(values) != len(cls._meta.concrete_fields):
            values_iter = iter(values)
            values = [
                next(values_iter) if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        new = cls(*values)
        new._state.adding = False
        new._state.db = db
        if fetch_mode is not None:
            new._state.fetch_mode = fetch_mode
        return new