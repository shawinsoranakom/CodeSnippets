def __init__(
        self, template, *args, extra_context=None, isolated_context=False, **kwargs
    ):
        self.template = template
        self.extra_context = extra_context or {}
        self.isolated_context = isolated_context
        super().__init__(*args, **kwargs)