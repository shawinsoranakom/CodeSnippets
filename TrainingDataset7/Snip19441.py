def _get_error_for_engine(self, engine):
        value = engine.engine.string_if_invalid
        return Error(
            "'string_if_invalid' in TEMPLATES OPTIONS must be a string but got: %r "
            "(%s)." % (value, type(value)),
            obj=engine,
            id="templates.E002",
        )