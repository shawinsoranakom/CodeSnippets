def __init__(self, attrs=None):
        choices = (
            ("unknown", _("Unknown")),
            ("true", _("Yes")),
            ("false", _("No")),
        )
        super().__init__(attrs, choices)