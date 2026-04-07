def __init__(self, fields, **kwargs):
        super().__init__(**kwargs)
        # Set 'required' to False on the individual fields, because the
        # required validation will be handled by ComboField, not by those
        # individual fields.
        for f in fields:
            f.required = False
        self.fields = fields