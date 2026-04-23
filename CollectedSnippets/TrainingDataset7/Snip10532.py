def __init__(
        self, app_label, name, fields, options=None, bases=None, managers=None
    ):
        self.app_label = app_label
        self.name = name
        self.fields = dict(fields)
        self.options = options or {}
        self.options.setdefault("indexes", [])
        self.options.setdefault("constraints", [])
        self.bases = bases or (models.Model,)
        self.managers = managers or []
        for name, field in self.fields.items():
            # Sanity-check that fields are NOT already bound to a model.
            if hasattr(field, "model"):
                raise ValueError(
                    'ModelState.fields cannot be bound to a model - "%s" is.' % name
                )
            # Ensure that relation fields are NOT referring to a model class.
            if field.is_relation and hasattr(field.related_model, "_meta"):
                raise ValueError(
                    'Model fields in "ModelState.fields" cannot refer to a model class '
                    f'- "{self.app_label}.{self.name}.{name}.to" does. Use a string '
                    "reference instead."
                )
            if field.many_to_many and hasattr(field.remote_field.through, "_meta"):
                raise ValueError(
                    'Model fields in "ModelState.fields" cannot refer to a model class '
                    f'- "{self.app_label}.{self.name}.{name}.through" does. Use a '
                    "string reference instead."
                )
        # Sanity-check that indexes have their name set.
        for index in self.options["indexes"]:
            if not index.name:
                raise ValueError(
                    "Indexes passed to ModelState require a name attribute. "
                    "%r doesn't have one." % index
                )