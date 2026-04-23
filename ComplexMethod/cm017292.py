def __init__(self, name, fields, options=None, bases=None, managers=None):
        self.fields = fields
        self.options = options or {}
        self.bases = bases or (models.Model,)
        self.managers = managers or []
        super().__init__(name)
        # Sanity-check that there are no duplicated field names, bases, or
        # manager names
        _check_for_duplicates("fields", (name for name, _ in self.fields))
        _check_for_duplicates(
            "bases",
            (
                (
                    base._meta.label_lower
                    if hasattr(base, "_meta")
                    else base.lower() if isinstance(base, str) else base
                )
                for base in self.bases
            ),
        )
        _check_for_duplicates("managers", (name for name, _ in self.managers))