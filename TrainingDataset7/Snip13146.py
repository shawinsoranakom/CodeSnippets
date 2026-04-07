def __init__(self, params):
        params = params.copy()
        options = params.pop("OPTIONS").copy()
        super().__init__(params)

        self.context_processors = options.pop("context_processors", [])

        environment = options.pop("environment", "jinja2.Environment")
        environment_cls = import_string(environment)

        if "loader" not in options:
            options["loader"] = jinja2.FileSystemLoader(self.template_dirs)
        options.setdefault("autoescape", True)
        options.setdefault("auto_reload", settings.DEBUG)
        options.setdefault(
            "undefined", jinja2.DebugUndefined if settings.DEBUG else jinja2.Undefined
        )

        self.env = environment_cls(**options)